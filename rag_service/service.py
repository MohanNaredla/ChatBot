import os
from data import Data

from typing import List, Dict, Optional
from pydantic import BaseModel
import uvicorn
import pickle
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import torch
from dotenv import load_dotenv

import openai
import tiktoken
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document

load_dotenv()
OPENAI_KEY = os.getenv('OPENAI_API_KEY')

app = FastAPI()
app.add_middleware(
    CORSMiddleware, 
    allow_origins = ["*"], 
    allow_headers = ["*"], 
    allow_methods = ["*"]
)

class TokenCounter:
    def __init__(self, model="gpt-3.5-turbo"):
        self.encoder = tiktoken.encoding_for_model(model)
        
    def count_tokens(self, text):
        tokens = self.encoder.encode(text)
        return len(tokens)

class Retrieve:
    def __init__(self, query):
        data = Data()
        self.faiss_dir = data.faiss_dir
        self.bm25_dir = data.bm25_dir
        self.top_k_retrieval = 8
        self.top_k_rerank = 4
        self.query = query
    
    def hybrid_retrieve(self):
        emb = SentenceTransformerEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
        vs = FAISS.load_local(self.faiss_dir, emb, allow_dangerous_deserialization=True)
        with open(self.bm25_dir, 'rb') as f:
            bm25, texts, metas = pickle.load(f)

        dense_docs = vs.similarity_search(self.query, self.top_k_retrieval)
        dense_doc_ids = {(d.metadata.get('section', ''), d.metadata.get('sub_section'), ''):d for d in dense_docs}

        tokenized_query = self.query.split()
        bm25_scores = bm25.get_scores(tokenized_query)
        all_indices = np.argsort(bm25_scores)
        bm25_top_indices = all_indices[::-1][:self.top_k_retrieval]

        bm25_chunks = []
        for idx in bm25_top_indices:
            meta = metas[idx]
            doc_id = (meta.get('section', ''), meta.get('sub_section'), '')
            if doc_id not in dense_doc_ids:
                bm25_chunks.append(Document(page_content=texts[idx], metadata=meta))

        combined_results = list(dense_doc_ids.values()) + bm25_chunks

        if len(combined_results) <= 2 * self.top_k_retrieval:
            return combined_results
        combined_results[:2 * self.top_k_retrieval]

        return combined_results
    
    def rerank(self, docs):
        rerank_tok = AutoTokenizer.from_pretrained('BAAI/bge-reranker-base')
        if torch.backends.mps.is_available():
            rerank_mod = AutoModelForSequenceClassification.\
            from_pretrained('BAAI/bge-reranker-base', d_type='float32').to('mps')

        elif torch.cuda.is_available():
            rerank_mod = AutoModelForSequenceClassification.\
                from_pretrained('BAAI/bge-reranker-base', torch_dtype='float32', device_map='auto')

        else:
            rerank_mod = AutoModelForSequenceClassification.from_pretrained('BAAI/bge-reranker-base').to('cpu')
        rerank_mod.eval()

        if len(docs) <= self.top_k_rerank:
            return docs
        
        with torch.no_grad():
            pairs = [[self.query, d.page_content] for d in docs]
            inp = rerank_tok(
                pairs,
                padding = True,
                truncation = True,
                return_tensors = 'pt',
                max_length = 512
            )
            inp = {k: v.to(rerank_mod.device) for k, v in inp.items()}
            scores = rerank_mod(**inp).logits.view(-1).cpu().numpy()

            return [docs[i] for i in np.argsort(scores)[::-1][:self.top_k_rerank]]

class Generation:
    def __init__(self, query, docs, conversation_context=None):
        self.query = query
        self.docs = docs
        self.conversation_context = conversation_context or []
        self.model = 'gpt-3.5-turbo'
        self.temperature = 0.35
        self.max_tokens = 500
        self.max_context_tokens = 700
        self.token_counter = TokenCounter(self.model)
        self.system_prompt = """
        You are a helpful assistant that provides accurate answers based on the given context.
        If the answer cannot be found in the context, say "I don't have enough information to answer this question.
        Do not make up information. Base your answer solely on the provided context.
        Be concise, natural, and don't reference document numbers.
        """

    def process_context(self):
        system_tokens = self.token_counter.count_tokens(self.system_prompt)
        
        docs_content = ''
        for i, doc in enumerate(self.docs):
            metadata = doc.metadata
            section = metadata.get('section', '')
            sub_section = metadata.get('subsection', '')
            header = f'{section}: {sub_section}' if section and sub_section else section or sub_section or ''
            docs_content += f"\n\n### Document {i+1}: {header}\n{doc.page_content}"
        
        docs_tokens = self.token_counter.count_tokens(docs_content)
        question_tokens = self.token_counter.count_tokens(self.query)
        
        remaining_tokens = self.max_context_tokens - system_tokens - docs_tokens - question_tokens - 20
        
        if remaining_tokens <= 0 or not self.conversation_context:
            return [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Context:\n{docs_content}\nQuestion: {self.query}"}
            ]
        
        all_history = []
        for exchange in self.conversation_context:
            all_history.append({
                "text": f"User: {exchange['question']}\nAssistant: {exchange['answer']}\n\n",
                "tokens": self.token_counter.count_tokens(f"User: {exchange['question']}\nAssistant: {exchange['answer']}\n\n")
            })
        
        history_header = "Previous conversation:\n"
        header_tokens = self.token_counter.count_tokens(history_header)
        remaining_tokens -= header_tokens
        
        final_history = []
        current_tokens = 0
        
        for exchange in reversed(all_history):
            if current_tokens + exchange["tokens"] <= remaining_tokens:
                final_history.insert(0, exchange["text"])
                current_tokens += exchange["tokens"]
            else:
                break
        
        history_text = history_header + ''.join(final_history) if final_history else ""
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Context:\n{docs_content}\n{history_text}\nQuestion: {self.query}"}
        ]
        
        return messages
    
    def generate_answer(self):
        openai.api_key = OPENAI_KEY

        messages = self.process_context()
        llm = openai.ChatCompletion.create(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            messages=messages
        )

        return llm.choices[0].message.content

class Query(BaseModel):
    question: str
    conversation_context: Optional[List[Dict[str, str]]] = None

@app.post('/chat')
async def ask_question(request: Query):
    retriever = Retrieve(query=request.question)
    retrieved_docs = retriever.rerank(retriever.hybrid_retrieve())
    
    generator = Generation(
        query=request.question, 
        docs=retrieved_docs,
        conversation_context=request.conversation_context
    )
    
    answer = generator.generate_answer()
    return {'question': request.question, 'answer': answer}

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)