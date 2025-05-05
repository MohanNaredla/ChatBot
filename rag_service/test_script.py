import json
import argparse
import time
import datetime
import os

import requests #type:ignore
import numpy as np
import torch #type:ignore
import pathlib
import pickle

from transformers import AutoTokenizer, AutoModelForSequenceClassification
from langchain_community.embeddings import SentenceTransformerEmbeddings #type:ignore
from langchain_community.vectorstores import FAISS #type:ignore
from langchain.schema import Document #type:ignore

def call_service(question):
    return requests.post("http://localhost:8000/chat", json={"question": question}).json()["answer"]

def inspect(question):
    return requests.post("http://localhost:8000/inspect", json={"question": question}).json()

def retrieve_chunks(question, top_k=2):
    emb = SentenceTransformerEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vs = FAISS.load_local("data/index/faiss", emb, allow_dangerous_deserialization=True)
    with open("data/index/bm25.pkl", "rb") as f:
        _, texts, metas = pickle.load(f)
    neigh = {(m["manual"], m["section"], m["sub_section"]): i for i, m in enumerate(metas)}
    dense = vs.similarity_search(question, k=top_k)
    flt = []
    ql = question.lower()
    if "district" in ql:
        flt.append("District")
    if "school" in ql:
        flt.append("School")
    if "ped" in ql:
        flt.append("PED")
    if flt:
        dense = [d for d in dense if any(f in d.metadata["manual"] for f in flt)] or dense
    expanded = list(dense)
    unique = {}
    for d in expanded:
        k = (d.metadata["manual"], d.metadata["section"], d.metadata["sub_section"])
        unique[k] = d
    candidates = list(unique.values())
    tok = AutoTokenizer.from_pretrained("BAAI/bge-reranker-base")
    mod = AutoModelForSequenceClassification.from_pretrained("BAAI/bge-reranker-base")
    pairs = [[question, d.page_content] for d in candidates]
    with torch.no_grad():
        inp = tok(pairs, padding=True, truncation=True, return_tensors="pt", max_length=512)
        scores = mod(**inp).logits.view(-1).numpy()
    top = [candidates[i] for i in np.argsort(scores)[::-1][:top_k]]
    return top

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--call_llm", action="store_true")
    parser.add_argument("--inspect", action="store_true")
    parser.add_argument("--questions", default="data/json/questions.json")
    args = parser.parse_args()

    questions = json.loads(open(args.questions, encoding="utf-8").read())
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    json_dir = pathlib.Path("data/json")
    json_dir.mkdir(parents=True, exist_ok=True)

    if args.call_llm:
        answers = {}
        for q in range(0, len(questions)):
            print(f"Asking question {q + 1}/{len(questions)}")
            que = questions[q]
            answers[que] = call_service(que)
            print(f"{que}: {answers[que]}")
            time.sleep(0.1)
        outfile = json_dir / f"answers_cache_{timestamp}.json"
        outfile.write_text(json.dumps(answers, indent=2, ensure_ascii=False), encoding="utf-8")
    
    elif args.inspect:
        chunks = {}
        for q in questions:
            chunks[q] = inspect(q)
        chunk_file = json_dir / f"llm_chunks_{timestamp}.json"
        chunk_file.write_text(json.dumps(chunks, indent=2, ensure_ascii=False), encoding="utf-8")
    
    else:
        all_chunks = {}
        for q in questions:
            retrieved = retrieve_chunks(q)
            all_chunks[q] = [
                {"metadata": d.metadata, "content": d.page_content} for d in retrieved
            ]
        outfile = json_dir / f"chunks_{timestamp}.json"
        outfile.write_text(json.dumps(all_chunks, indent=2, ensure_ascii=False), encoding="utf-8")

if __name__ == "__main__":
    main()
