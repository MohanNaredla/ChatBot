import os, glob, re, pickle, fitz, numpy as np #type:ignore
from rank_bm25 import BM25Okapi  # type:ignore
from langchain_community.embeddings import SentenceTransformerEmbeddings  # type:ignore
from langchain_community.vectorstores import FAISS  # type:ignore
from langchain.schema import Document  # type:ignore

paths = glob.glob("data/manuals/*.pdf")
docs, rec = [], []

sec_re = re.compile(r'^\d+\.\s+[A-Z].{5,}$')
sub_re = re.compile(r'^\d+\.\d+\s+[A-Z]')
app_re = re.compile(r'^[A-Z]\.\s+[A-Z]')

intro_added = False

def role_name(manual: str):
    return manual.replace("UserManual", "").replace("User Manual", "").replace("Manual", "").strip("_ ")

for pdf in paths:
    name = os.path.basename(pdf).rsplit(".", 1)[0]
    doc = fitz.open(pdf)
    lines, sizes = [], []
    for pg in doc[2:]:
        data = pg.get_text("dict")
        for blk in data["blocks"]:
            if "lines" not in blk:
                continue
            for ln in blk["lines"]:
                txt = "".join(s["text"] for s in ln["spans"]).strip()
                if not txt:
                    continue
                if re.match(r"^Page\s+\d+\s+of\s+\d+", txt):
                    continue
                if re.match(r"^BVM,.*Attendance Improvement Plan", txt):
                    continue
                if re.match(r"^[\s\-–_=]+$", txt):
                    continue
                fsz = max(s["size"] for s in ln["spans"])
                lines.append((pg.number + 1, txt, fsz))
                sizes.append(fsz)
    doc.close()
    if not lines:
        continue
    cand_hdr = [fsz for _, t, fsz in lines if sec_re.match(t)]
    header_size = max(cand_hdr) if cand_hdr else np.percentile(sizes, 95)
    idx = [i for i, (_, t, f) in enumerate(lines) if (f >= header_size - 0.5) and (sec_re.match(t) or app_re.match(t))]
    idx.append(len(lines))

    for i in range(len(idx) - 1):
        s, e = idx[i], idx[i + 1]
        seg = lines[s:e]
        hdr = seg[0][1]
        if app_re.match(hdr):
            sec_num, sec_title = hdr.split(" ", 1)
            sec_clean = sec_num.rstrip(".")
        else:
            sec_num, sec_title = hdr.split(" ", 1)
            sec_clean = sec_num.rstrip(".")

        sub_idx = [j for j in range(1, len(seg)) if sub_re.match(seg[j][1])]
        sub_idx.append(len(seg))

        def make_meta(pg, sub_num="", sub_title=""):
            meta = {
                "manual": name,
                "page": pg,
                "section": sec_clean,
                "section_title": sec_title.strip(),
                "sub_section": sub_num,
                "sub_title": sub_title.strip()
            }
            if sec_title.strip() == "Introduction":
                if intro_added:
                    return None
                meta["manual"] = "AllManualsIntro"
                meta["role"] = "General"
            else:
                if name == "PED Roles UserManual":
                    meta["role"] = sec_title.strip()
                else:
                    meta["role"] = role_name(name)
            return meta

        if len(sub_idx) > 1:
            for k in range(len(sub_idx) - 1):
                a, b = sub_idx[k], sub_idx[k + 1]
                sub_hdr = seg[a][1]
                sub_num, sub_title = sub_hdr.split(" ", 1)
                text = "\n".join(t for _, t, _ in seg[a:b])
                pg = seg[a][0]
                meta = make_meta(pg, sub_num, sub_title)
                if meta:
                    if meta["manual"] == "AllManualsIntro":
                        intro_added = True
                    docs.append(Document(page_content=text, metadata=meta))
                    rec.append((meta, text))
        else:
            text = "\n".join(t for _, t, _ in seg)
            pg = seg[0][0]
            meta = make_meta(pg)
            if meta:
                if meta["manual"] == "AllManualsIntro":
                    intro_added = True
                docs.append(Document(page_content=text, metadata=meta))
                rec.append((meta, text))

os.makedirs("data/index", exist_ok=True)
with open("data/index/chunks_with_metadata.txt", "w", encoding="utf-8") as f:
    for m, t in rec:
        f.write(f"{m}\n{t}\n{'='*60}\n")

emb = SentenceTransformerEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")  # type:ignore
vs = FAISS.from_documents(docs, emb)
vs.save_local("data/index/faiss")

texts = [d.page_content for d in docs]
bm25 = BM25Okapi([t.split() for t in texts])
meta = [d.metadata for d in docs]
with open("data/index/bm25.pkl", "wb") as f:
    pickle.dump((bm25, texts, meta), f)
