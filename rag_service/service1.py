import os
import string
import re
import difflib
import sys
from collections import defaultdict
import json
from datetime import time

from pydantic import BaseModel
import uvicorn
import pickle
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import torch
from dotenv import load_dotenv

import openai
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


load_dotenv()
OPENAI_KEY = os.getenv('OPENAI_API_KEY')


class Retrieve:
    def __init__(self, query):
        self.top_k_retrieval = 8
        self.top_k_rerank = 4
        self.vs_path = 'data/index/faiss'
        self.bm_path = 'data/index/bm25.pkl'
        self.query = query
        
    
    def hybrid_retrieve(self):
        emb = SentenceTransformerEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
        vs = FAISS.load_local(self.vs_path, emb, allow_dangerous_deserialization=True)
        with open(self.bm_path, 'rb') as f:
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
    def __init__(self, query, docs):
        self.query = query
        self.docs = docs
        self.model = 'gpt-3.5-turbo'
        self.temperature = 0.3
        self.top_p = 0.85
        self.max_tokens = 500
        self.system_prompt =  """You are a helpful assistant that provides accurate answers based on the given context.
        If the answer cannot be found in the context, say "I don't have enough information to answer this question.
        Do not make up information. Base your answer solely on the provided context."""


    def process_context(self):
        content = ''
        for i, doc in enumerate(self.docs):
            metadata = doc.metadata
            section = metadata.get('section', '')
            sub_section = metadata.get('subsection', '')
            header = f'{section}: {sub_section}' if section and sub_section else section or sub_section or ''
            content += f"\n\n### Document {i+1}: {header}\n{doc.page_content}"

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Context:\n{content}\n\nQuestion: {self.query}"}
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

query =  "What are the password requirements and how often should we create a new password?"
retriever = Retrieve(query=query)
docs = retriever.rerank(retriever.hybrid_retrieve())
generator = Generation(docs=docs, query=query)
print(generator.generate_answer())