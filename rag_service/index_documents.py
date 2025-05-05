import os, glob, re, pickle
from rank_bm25 import BM25Okapi #type:ignore 
from langchain_community.embeddings import SentenceTransformerEmbeddings #type:ignore
from langchain_community.vectorstores import FAISS #type:ignore
from langchain.schema import Document #type:ignore

paths = glob.glob("data/manuals/*.txt")
docs, rec = [], []

sec_re = re.compile(r'^\d+\.\s+[A-Z].{5,}')
sub_re = re.compile(r'^\d+\.\d+\s+[A-Z]')
app_re = re.compile(r'^[A-Z]\.\s+[A-Z]')

for txt_file in paths:
    name = os.path.basename(txt_file).rsplit(".", 1)[0]
    
    with open(txt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    all_lines = [line for line in content.split('\n') if line.strip()]
    
    section_indices = [i for i, line in enumerate(all_lines) if sec_re.match(line) or app_re.match(line)]
    
    if not section_indices:
        continue
        
    section_indices.append(len(all_lines))
    
    for i in range(len(section_indices) - 1):
        start_idx, end_idx = section_indices[i], section_indices[i + 1]
        section_content = all_lines[start_idx:end_idx]
        
        section_header = section_content[0]
        
        if app_re.match(section_header):
            sec_num, sec_title = section_header.split(" ", 1)
            sec_clean = sec_num.rstrip(".")
        else:
            sec_num, sec_title = section_header.split(" ", 1)
            sec_clean = sec_num.rstrip(".")
        
        subsection_indices = [j for j, line in enumerate(section_content) if j > 0 and sub_re.match(line)]
        
        if subsection_indices:
            subsection_indices.append(len(section_content))
            
            for k in range(len(subsection_indices) - 1):
                sub_start, sub_end = subsection_indices[k], subsection_indices[k + 1]
                sub_content = section_content[sub_start:sub_end]
                
                sub_header = sub_content[0]
                sub_num, sub_title = sub_header.split(" ", 1)
                
                text_content = "\n".join(sub_content)
                
                if sec_title.strip() in ("Introduction", "Support & Troubleshooting"):
                    continue
                    
                meta = {
                    "manual": name,
                    "section": sec_clean,
                    "section_title": sec_title.strip(),
                    "sub_section": sub_num,
                    "sub_title": sub_title.strip()
                }
                
                docs.append(Document(page_content=text_content, metadata=meta))
                rec.append((meta, text_content))
        else:
            text_content = "\n".join(section_content)
            
            if sec_title.strip() in ("Introduction", "Support & Troubleshooting"):
                continue
                
            meta = {
                "manual": name,
                "section": sec_clean,
                "section_title": sec_title.strip(),
                "sub_section": "",
                "sub_title": ""
            }
            
            docs.append(Document(page_content=text_content, metadata=meta))
            rec.append((meta, text_content))

os.makedirs("data/index", exist_ok=True)
with open("data/index/chunks_with_metadata.txt", "w", encoding="utf-8") as f:
    for m, t in rec:
        f.write(f"{m}\n{t}\n{'='*60}\n")

emb = SentenceTransformerEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vs = FAISS.from_documents(docs, emb)
vs.save_local("data/index/faiss")

texts = [d.page_content for d in docs]
bm25 = BM25Okapi([t.split() for t in texts])
meta = [d.metadata for d in docs]
with open("data/index/bm25.pkl", "wb") as f:
    pickle.dump((bm25, texts, meta), f)