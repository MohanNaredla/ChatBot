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

pdf_directory = "data/manuals/"
pdf_files = glob.glob(f"{pdf_directory}*.pdf")

if not pdf_files:
    sys.exit(f"No PDF files found in {pdf_directory}")

all_chunks = []

for pdf_path in pdf_files:
    if not os.path.exists(pdf_path):
        continue

    doc = fitz.open(pdf_path)
    text = "".join(page.get_text() + "\n" for page in doc)
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

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", " ", ""]
    )
    pdf_chunks = [
        chunk
        for section in sections
        for chunk in splitter.split_text(section)
        if chunk.strip()
    ]
    all_chunks.extend(pdf_chunks)

if not all_chunks:
    sys.exit("No chunks generated from any PDF files")

embedding = SentenceTransformerEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
vectorstore = FAISS.from_texts(all_chunks, embedding)

os.makedirs("data/index", exist_ok=True)
vectorstore.save_local("data/index/faiss")

tokenized = [chunk.split() for chunk in all_chunks]
bm25 = BM25Okapi(tokenized)
with open("data/index/bm25.pkl", "wb") as f:
    pickle.dump((bm25, all_chunks), f)

print(f"Successfully indexed {len(all_chunks)} chunks")
print("FAISS index saved to data/index/faiss")
print("BM25 index saved to data/index/bm25.pkl")