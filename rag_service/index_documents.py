import os
import sys
import glob
import re
import pickle
import fitz #type:ignore

from langchain_community.embeddings import SentenceTransformerEmbeddings #type:ignore
from langchain.text_splitter import RecursiveCharacterTextSplitter #type:ignore
from langchain_community.vectorstores import FAISS #type:ignore
from rank_bm25 import BM25Okapi #type:ignore

pdf_path = "data/manuals/PEDRolesUserManual.pdf"
if not os.path.exists(pdf_path):
    sys.exit(f"File not found: {pdf_path}")

doc = fitz.open(pdf_path)
text = "".join(p.get_text() + "\n" for p in doc)
doc.close()

lines = text.replace("\r", "\n").splitlines()
sections = []
cur = []
for line in lines:
    if re.match(r"^\d+(\.\d+)*\s", line):
        if cur:
            sections.append("\n".join(cur).strip())
        cur = [line]
    else:
        cur.append(line)
if cur:
    sections.append("\n".join(cur).strip())

splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100, separators=["\n\n", "\n", " ", ""])
chunks = [c for sec in sections for c in splitter.split_text(sec) if c.strip()]
if not chunks:
    sys.exit("no chunks generated")

embedding = SentenceTransformerEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = FAISS.from_texts(chunks, embedding)
vectorstore.save_local("data/index/faiss")

tokenized = [c.split() for c in chunks]
bm25 = BM25Okapi(tokenized)
with open("data/index/bm25.pkl", "wb") as f:
    pickle.dump((bm25, chunks), f)

print(f"indexed {len(chunks)} chunks")
