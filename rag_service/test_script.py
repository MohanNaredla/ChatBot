import json, os, subprocess, re, time, importlib, sys, torch

def branch():
    try:
        return subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode().strip()
    except Exception:
        return "unknown"

def n(t): return re.sub(r"[^a-z0-9]+", " ", t.lower()).split()

def ov(a, b):
    d1, d2, o = {}, {}, 0
    [d1.setdefault(t, 0) or d1.__setitem__(t, d1[t] + 1) for t in a]
    [d2.setdefault(t, 0) or d2.__setitem__(t, d2[t] + 1) for t in b]
    for t, c in d1.items():
        if t in d2: o += min(c, d2[t])
    return o

def main():
    br = branch()
    svc = importlib.import_module("service")
    top_k = getattr(svc, "TOP_K", 5)
    tf = "data/json/test_questions.json"
    of = f"data/json/test_results_{br}.json"
    cf = f"data/json/cache_{br}.json"
    td = json.load(open(tf))
    cache = json.load(open(cf)) if os.path.exists(cf) else {}
    res = []
    for e in td:
        q, exp, kw = e["question"], e["expected_answer"], e.get("keywords")
        if q in cache:
            ans = cache[q]
        else:
            ans = svc.generate_answer(q)
            cache[q] = ans
        t0 = time.time()
        ctx = "\n".join(svc.hybrid_retrieve(q, top_k))
        rt = time.time() - t0
        at, et, ct = n(ans), n(exp), n(ctx)
        oa, oc = ov(at, et), ov(ct, et)
        p = oa / len(at) if at else 0
        r = oa / len(et) if et else 0
        f1 = 2 * p * r / (p + r) if p + r else 0
        cp = oc / len(ct) if ct else 0
        cr = oc / len(et) if et else 0
        ac = ov(at, ct)
        faithful = ac / len(at) if at else 1
        hall = 1 - faithful
        if ans.lower().startswith("i can't answer"):
            faithful, hall = 1, 0
        km = {}
        if kw:
            kwl = [k.lower() for k in kw]
            km = {
                "keywords_covered_in_answer": len([k for k in kwl if k in ans.lower()]),
                "keywords_covered_in_context": len([k for k in kwl if k in ctx.lower()]),
                "total_keywords": len(kwl)
            }
        m = {
            "answer_precision": round(p, 3),
            "answer_recall": round(r, 3),
            "answer_f1": round(f1, 3),
            "context_precision": round(cp, 3),
            "context_recall": round(cr, 3),
            "faithfulness": round(faithful, 3),
            "hallucination_rate": round(hall, 3),
            "retrieval_latency_seconds": round(rt, 4)
        }
        m.update(km)
        res.append({"question": q, "expected_answer": exp, "model_answer": ans, "metrics": m})
    os.makedirs("data/json", exist_ok=True)
    json.dump(res, open(of, "w"), indent=2)
    json.dump(cache, open(cf, "w"), indent=2)
    avg = sum(x["metrics"]["answer_f1"] for x in res) / len(res)
    print(f"{br} average answer_F1: {round(avg,3)}  -> {of}")

if __name__ == "__main__":
    main()
