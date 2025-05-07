import os
import string
import sys
import re
from collections import defaultdict
import json
from datetime import time
import difflib

import pickle
import numpy as np
import torch #type:ignore
from fastapi import FastAPI #type:ignore
from fastapi.middleware.cors import CORSMiddleware #type:ignore
import uvicorn #type:ignore
from pydantic import BaseModel #type:ignore

from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModelForSequenceClassification
from langchain_community.embeddings import SentenceTransformerEmbeddings #type:ignore
from langchain_community.vectorstores import FAISS #type:ignore
from langchain.schema import Document #type:ignore
from huggingface_hub import login #type:ignore
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


token = os.getenv("HF_TOKEN")
if token:
    login(token=token)

class Query(BaseModel):
    question: str
    

emb = SentenceTransformerEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vs = FAISS.load_local("data/index/faiss", emb, allow_dangerous_deserialization=True)
with open("data/index/bm25.pkl", "rb") as f:
    bm25, texts, metas = pickle.load(f)
neighbor = {(m["manual"], m["section"], m["sub_section"]): i for i, m in enumerate(metas)}

rerank_tok = AutoTokenizer.from_pretrained("BAAI/bge-reranker-base")
if torch.backends.mps.is_available():
    rerank_mod = AutoModelForSequenceClassification.from_pretrained("BAAI/bge-reranker-base", torch_dtype=torch.float32).to("mps")
elif torch.cuda.is_available():
    rerank_mod = AutoModelForSequenceClassification.from_pretrained("BAAI/bge-reranker-base", device_map="auto", torch_dtype=torch.float16)
else:
    rerank_mod = AutoModelForSequenceClassification.from_pretrained("BAAI/bge-reranker-base").to("cpu")
rerank_mod.eval()

llm_tok = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2", use_auth_token=token)
llm = AutoModelForCausalLM.from_pretrained(
    "mistralai/Mistral-7B-Instruct-v0.2",
    device_map="auto" if torch.cuda.is_available() else "cpu",
    torch_dtype=torch.float16 if torch.cuda.is_available() else None,
    use_auth_token=token,
    low_cpu_mem_usage=True,
)
llm.eval()

def retrieve(query: str, k: int = 2):
    dense = vs.similarity_search(query, k=k)
    with torch.no_grad():
        pairs = [[query, d.page_content] for d in dense]
        inp = rerank_tok(
            pairs,
            padding=True,
            truncation=True,
            return_tensors="pt",
            max_length=512,
        )
        inp = {k: v.to(rerank_mod.device) for k, v in inp.items()}
        scores = rerank_mod(**inp).logits.view(-1).cpu().numpy()
    return [dense[i] for i in np.argsort(scores)[::-1][:k]]

def organize(docs, query):
    sorted_docs = sorted(docs, key=lambda d: (
        d.metadata.get("section", ""), 
        d.metadata.get("sub_section", "")
    ))
    
    return sorted_docs

def clean_unicode_spaces(text):
    if text is None:
        return None
    return text.replace('\u202f', ' ')

def build_prompt(question: str, docs):
    organized_docs = organize(docs, question)
    if not organized_docs:
        return "I don't have enough information about this. Please contact the support staff for assistance.", []

    ctx_blocks = []
    for i, d in enumerate(organized_docs):
        m = d.metadata
        
        section_title = clean_unicode_spaces(m.get('section_title', ''))
        sub_title = clean_unicode_spaces(m.get('sub_title', ''))
        
        section = f"SECTION {m.get('section', 'N/A')}: {section_title}"
        if m.get('sub_section'):
            section += f"\nSUBSECTION {m['sub_section']}: {sub_title}"
            
        header = f"[CONTEXT BLOCK {i + 1}]\n{section}"
        ctx_blocks.append(f"{header}\n\nCONTENT:\n{d.page_content.strip()}")

    context = "\n\n" + "=" * 50 + "\n\n".join(ctx_blocks) + "\n\n" + "=" * 50 + "\n"

    system_prompt = (
        "You are a helpful assistant with access to an Attendance Improvement Plan (AIP) knowledge base.\n\n"
        "When answering:\n"
        "- Be extremely concise and direct.\n"
        "- Only include information that directly answers the specific question asked.\n"
        "- Avoid providing extra details, background information, or tangential points.\n"
        "- Stick strictly to information found in the provided context.\n"
        "- If the information needed isn't in the context, simply say so briefly.\n"
        "- Format your response in short, simple sentences with minimal text."
    )

    prompt = f"{system_prompt}\n\nQUESTION:\n{question}\n\nCONTEXT:{context}\n\nANSWER:\n"
    return prompt, organized_docs

def generate_answer(question: str):
    docs = retrieve(question)
    
    if not docs:
        return "I don't have enough information about this. Please contact the support staff for assistance."
    
    prompt, organised_docs = build_prompt(question, docs)
    
    inp = llm_tok(prompt, return_tensors="pt")
    if torch.cuda.is_available():
        inp = {k: v.to(llm.device) for k, v in inp.items()}
    
    out = llm.generate(**inp, max_new_tokens=512, do_sample=False, temperature=0.15, top_p=0.9)
    answer = llm_tok.decode(out[0][inp["input_ids"].shape[1]:], skip_special_tokens=True).strip()
    
    answer = re.sub(r'#QUESTION.*?#ANSWER', '', answer, flags=re.DOTALL)
    answer = re.sub(r'#QUESTION|#ANSWER', '', answer)
    
    if not answer or "I don't have enough information" in answer:
        return "I don't have enough information about this. Please contact the support staff for assistance."
    
    return answer

def inspect_chunks(question: str):
    docs = retrieve(question)
    prompt, organized_docs = build_prompt(question, docs)
    
    serializable_docs = []
    for doc in organized_docs:
        serializable_doc = {
            "content": doc.page_content,
            "metadata": {}
        }
        for k, v in doc.metadata.items():
            if isinstance(v, (str, int, float, bool, list)) or v is None:
                if isinstance(v, str):
                    v = clean_unicode_spaces(v)
                serializable_doc["metadata"][k] = v
            else:
                serializable_doc["metadata"][k] = str(v)
        serializable_docs.append(serializable_doc)
    
    original_docs = []
    for doc in docs:
        orig_doc = {
            "content": doc.page_content,
            "metadata": {}
        }
        for k, v in doc.metadata.items():
            if isinstance(v, (str, int, float, bool, list)) or v is None:
                if isinstance(v, str):
                    v = clean_unicode_spaces(v)
                orig_doc["metadata"][k] = v
            else:
                orig_doc["metadata"][k] = str(v)
        original_docs.append(orig_doc)
    
    return {
        "question": question,
        "prompt": prompt,
        "original_docs": original_docs,
        "organized_docs": serializable_docs
    }

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.post("/chat")
def chat(r: Query):
    return {"question": r.question, "answer": generate_answer(r.question)}

@app.post("/inspect")
def inspect(r: Query):
    return {"inspection": inspect_chunks(r.question)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)