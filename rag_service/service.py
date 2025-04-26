import os
import pickle
import numpy as np
from dotenv import load_dotenv #type:ignore

import torch #type:ignore
from fastapi import FastAPI #type:ignore
import uvicorn #type:ignore
from pydantic import BaseModel #type:ignore
from huggingface_hub import login #type:ignore

from transformers import AutoTokenizer, AutoModelForCausalLM
from langchain_community.embeddings import SentenceTransformerEmbeddings #type:ignore
from langchain_community.vectorstores import FAISS #type:ignore

load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
if HF_TOKEN:
    login(token=HF_TOKEN)

class QueryRequest(BaseModel):
    question: str

embedding = SentenceTransformerEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = FAISS.load_local("data/index/faiss", embedding, allow_dangerous_deserialization=True)
with open("data/index/bm25.pkl", "rb") as f:
    bm25, chunks_list = pickle.load(f)

model_name = "mistralai/Mistral-7B-Instruct-v0.2"
tokenizer = AutoTokenizer.from_pretrained(model_name, use_auth_token=HF_TOKEN)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="auto" if torch.cuda.is_available() else None,
    torch_dtype=torch.float16 if torch.cuda.is_available() else None,
    use_auth_token=HF_TOKEN
)
model.eval()

def hybrid_retrieve(query: str, top_k: int = 5):
    dense_docs = vectorstore.similarity_search(query, k=top_k)
    dense_texts = [d.page_content for d in dense_docs]
    sparse_scores = bm25.get_scores(query.split())
    sparse_idxs = np.argsort(sparse_scores)[::-1][:top_k]
    sparse_texts = [chunks_list[i] for i in sparse_idxs]
    combined, seen = [], set()
    for txt in dense_texts + sparse_texts:
        if txt not in seen:
            combined.append(txt)
            seen.add(txt)
    return combined[:top_k]

def generate_answer(query: str):
    ctx = "\n".join(hybrid_retrieve(query, 5))
    prompt = (
        "### Instruction:\n"
        "Answer the question using the context below. If the answer is not in the context, say \"I can't answer that as it is not within the scope and say nothing else\".\n\n"
        f"### Context:\n{ctx}\n\n"
        f"### Question:\n{query}\n\n"
        "### Response:"
    )
    inputs = tokenizer(prompt, return_tensors="pt")
    if torch.cuda.is_available():
        inputs = {k: v.to(model.device) for k, v in inputs.items()}
    out = model.generate(**inputs, max_new_tokens=256, do_sample=False)
    return tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()

app = FastAPI()

@app.post("/chat")
def chat(req: QueryRequest):
    return {"question": req.question, "answer": generate_answer(req.question)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
