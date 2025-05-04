import os
import sys
import re
from collections import defaultdict
import json
from datetime import time

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

ROLES = [
    "District Absence Coordinator",
    "School Absence Coordinator",
    "PED Absence Coordinator",
    "PED Viewer",
    "IT Administrator",
]
ROLE_REGEX = re.compile("|".join([re.escape(r.lower()) for r in ROLES]))

def retrieve(query: str, k: int = 5):
    q_lower = query.lower()
    if ("how" in q_lower and "update" in q_lower and "progress" in q_lower and 
        ("reporting" in q_lower or "period" in q_lower)):
        progress_docs = []
        for i, meta in enumerate(metas):
            if meta["sub_title"] == "Step 6: Progress Updates":
                progress_docs.append(Document(page_content=texts[i], metadata=meta))
        if progress_docs:
            return progress_docs[:k]
    
    manual_filter = []
    if "district" in q_lower:
        manual_filter.append("District")
    if "school" in q_lower:
        manual_filter.append("School")
    if "ped" in q_lower:
        manual_filter.append("PED")
    dense = vs.similarity_search(query, k=k)
    if manual_filter:
        dense = [d for d in dense if any(f in d.metadata["manual"] for f in manual_filter)] or dense
    expanded = list(dense)
    for d in dense:
        m, s, sub = d.metadata["manual"], d.metadata["section"], d.metadata["sub_section"]
        if sub:
            try:
                n = int(sub.split(".")[1])
            except (IndexError, ValueError):
                continue
            for nn in (n - 1, n + 1):
                key = (m, s, f"{s}.{nn}")
                if key in neighbor:
                    idx = neighbor[key]
                    expanded.append(Document(page_content=texts[idx], metadata=metas[idx]))
    uniq = {}
    for d in expanded:
        key = (d.metadata["manual"], d.metadata["section"], d.metadata["sub_section"])
        uniq[key] = d
    candidates = list(uniq.values())
    with torch.no_grad():
        pairs = [[query, d.page_content] for d in candidates]
        inp = rerank_tok(pairs, padding=True, truncation=True, return_tensors="pt", max_length=512)
        inp = {k: v.to(rerank_mod.device) for k, v in inp.items()}
        scores = rerank_mod(**inp).logits.view(-1).cpu().numpy()
    top_docs = [candidates[i] for i in np.argsort(scores)[::-1][:k]]
    return top_docs

def deduplicate_and_organize(docs):
    content_groups = defaultdict(list)
    for doc in docs:
        simplified = re.sub(r'\s+', ' ', doc.page_content.lower().strip())
        simplified = re.sub(r'[^a-z0-9\s]', '', simplified)
        content_groups[simplified].append(doc)
    
    deduplicated_docs = []
    for content_group in content_groups.values():
        if len(content_group) == 1:
            deduplicated_docs.append(content_group[0])
        else:
            roles = [doc.metadata["role"] for doc in content_group]
            best_doc = max(content_group, key=lambda d: len(d.page_content))
            combined_metadata = best_doc.metadata.copy()
            combined_metadata["roles"] = roles
            deduplicated_docs.append(Document(
                page_content=best_doc.page_content,
                metadata=combined_metadata
            ))
    
    deduplicated_docs.sort(key=lambda d: (
        d.metadata.get("section", ""), 
        d.metadata.get("sub_section", "")
    ))
    
    return deduplicated_docs

def build_prompt(question: str, docs):
    organized_docs = deduplicate_and_organize(docs)
    
    ctx_blocks = []
    for d in organized_docs:
        metadata = d.metadata
        roles = metadata.get("roles", [metadata.get("role")])
        
        header = f"[SECTION: {metadata.get('section', '')} | SUB_SECTION: {metadata.get('sub_section', '')} | SUB_TITLE: {metadata.get('sub_title', '')}]"
        
        if len(roles) > 1:
            roles_str = ", ".join(roles)
            header += f"\n[APPLICABLE TO ROLES: {roles_str}]"
        else:
            header += f"\n[ROLE: {roles[0]}]"
            
        ctx_blocks.append(f"{header}\n{d.page_content}")
    
    context = "\n\n---\n\n".join(ctx_blocks)
    
    system_instr = (
        "You are an attendance-policy assistant that answers questions about the Attendance Improvement Plan system. "
        "Follow these rules precisely:\n\n"
        "1. Address the user directly in the second person ('you should...' not 'I can...').\n"
        "2. Use ONLY information contained in the CONTEXT section.\n"
        "3. Provide exact navigation paths, field names, and button labels exactly as written in the manuals.\n"
        "4. Preserve hierarchical relationships between sections and subsections.\n"
        "5. For role-specific information:\n"
        "   - If the question explicitly mentions a role, answer only for that role.\n"
        "   - If the question does not mention a role and context contains information for multiple roles:\n"
        "     - IF the information is identical across roles, provide a SINGLE answer without role prefixes.\n"
        "     - IF the information differs between roles, be creative in how you introduce each role's perspective (using phrases like 'As a {role}...', 'For {role} users...', 'From the {role} perspective...', etc.).\n"
        "   - If the question does not mention a role and only one role is in context, answer directly without mentioning the role.\n"
        "6. Keep answers concise and direct - do not add unnecessary explanations unless asked.\n"
        "7. Never use first-person perspective (no 'I', 'me', 'my').\n"
        "8. Never include development markers like '#QUESTION' or '#ANSWER' in your response.\n"
        "9. Do NOT invent steps or information not present in the context."
    )
    
    prompt = f"{system_instr}\n\n### CONTEXT\n{context}\n\n### QUESTION\n{question}\n\n### ANSWER\n"
    return prompt, organized_docs

def generate_answer(question: str):
    docs = retrieve(question)
    prompt = build_prompt(question, docs)
    inp = llm_tok(prompt, return_tensors="pt")
    if torch.cuda.is_available():
        inp = {k: v.to(llm.device) for k, v in inp.items()}
    out = llm.generate(**inp, max_new_tokens=384, do_sample=False, temperature=0.0, top_p=0.9)
    answer = llm_tok.decode(out[0][inp["input_ids"].shape[1]:], skip_special_tokens=True).strip()
    
    answer = re.sub(r'#QUESTION.*?#ANSWER', '', answer, flags=re.DOTALL)
    answer = re.sub(r'#QUESTION|#ANSWER', '', answer)
    
    answer = re.sub(r'\bI can\b', 'You can', answer)
    answer = re.sub(r'\bI will\b', 'You can', answer)
    answer = re.sub(r'\bI would\b', 'You can', answer)
    answer = re.sub(r'\bI am\b', 'You are', answer)
    answer = re.sub(r'\bmy\b', 'your', answer)
    
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
                serializable_doc["metadata"][k] = v
            else:
                serializable_doc["metadata"][k] = str(v)
        serializable_docs.append(serializable_doc)
    
    return {
        "question": question,
        "prompt": prompt,
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