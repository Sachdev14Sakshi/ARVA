
from datetime import date, datetime
from app.models.case import getCases
from app.llm.client import call_llm
from app.db.chroma_client import init_chromadb
import openai
from openai import OpenAI
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter


def norm_date(x):
    if not x: return None
    if isinstance(x, datetime): return x.date()
    if isinstance(x, date):     return x
    try: return date.fromisoformat(x)
    except: return None

def fmt_meta(md):
    d = date.fromordinal(md["_ord"])
    m = dict(md)
    m["date"] = d.isoformat()
    return m

def to_date_or_none(v):
    if v is None or v == "": return None
    return norm_date(v)

VALID_ANIMALS   = sorted({c["metadata"]["animal"]   for c in getCases()})
VALID_LOCATIONS = sorted({c["metadata"]["location"] for c in getCases()})
VALID_STATUSES  = sorted({c["metadata"]["status"]   for c in getCases()})

def detect_filters(q, valid):
    ql = q.lower()
    return [v for v in valid if v.lower() in ql]

def detect_potential(query: str, valid_set: set[str]) -> list[str]:
    """Return all valid_set items whose name appears in query (case-insensitive)."""
    q = query.lower()
    return [x for x in valid_set if x.lower() in q]

def generate_report(start_cal, end_cal):
    sd = to_date_or_none(start_cal)
    ed = to_date_or_none(end_cal)
    sd_ord = sd.toordinal() if sd else None
    ed_ord = ed.toordinal() if ed else None
    selected = []
    for c in getCases():
        o = date.fromisoformat(c['metadata']['date']).toordinal()
        if sd_ord and o < sd_ord: continue
        if ed_ord and o > ed_ord: continue
        selected.append(c)
    if not selected:
        return "No cases found in that date range."
    # Build report with Summary column
    header = "Case ID | Animal | Date | Status | Summary"
    lines = []
    for c in selected:
        lines.append(
            f"{c['case_id']} | {c['metadata']['animal']} | {c['metadata']['date']} | {c['metadata']['status']} | {c['text']}"
        )
    report = "\n".join([header] + lines)
    return report


def perform_search(api_key, query, start_cal, end_cal):
    logs = [f"[DEBUG] semantic search() called with {query!r}"]
    if not api_key:
        return logs, "", "⚠️ Missing API key."
    openai.api_key = api_key

    ql = query.lower()

    # 1) Normalize dates
    sd = to_date_or_none(start_cal)
    ed = to_date_or_none(end_cal)
    sd_ord = sd.toordinal() if sd else None
    ed_ord = ed.toordinal() if ed else None
    logs.append(f"[DEBUG] date window ord: {sd_ord}→{ed_ord}")

    # 2) detect everything mentioned
    mentioned_animals = detect_potential(query, VALID_ANIMALS)
    mentioned_locations = detect_potential(query, VALID_LOCATIONS)
    mentioned_statuses = detect_potential(query, VALID_STATUSES)

    # 3) Detect metadata filters
    af = detect_filters(query, VALID_ANIMALS)
    lf = detect_filters(query, VALID_LOCATIONS)
    sf = detect_filters(query, VALID_STATUSES)
    hv = "video" in query.lower() or "has_video" in query.lower()

    logs.append(f"[DEBUG] date window ord: {mentioned_animals}→{ed_ord}")

    missing = []
    if mentioned_animals and not af: missing.append(f"animal(s) {mentioned_animals!r}")
    if mentioned_locations and not lf: missing.append(f"location(s) {mentioned_locations!r}")
    if mentioned_statuses and not sf: missing.append(f"status(es) {mentioned_statuses!r}")
    if missing:
        return logs, "", f"No cases for {', '.join(missing)}."

    conds = []
    if sd_ord is not None:
        conds.append({"_ord": {"$gte": sd_ord}})
    if ed_ord is not None:
        conds.append({"_ord": {"$lte": ed_ord}})
    if af:
        conds.append({"animal": af[0]})
    if lf:
        conds.append({"location": lf[0]})
    if sf:
        conds.append({"status": sf[0]})
    if hv:
        conds.append({"has_video": True})

    where = {"$and": conds} if conds else None
    logs.append(f"[DEBUG] metadata where clause: {where}")
    collection, embed_model = init_chromadb()
    # 4) Semantic lookup with metadata filter in‐DB
    vec = embed_model.encode([query]).tolist()
    resp = collection.query(
        query_embeddings=vec,
        n_results=10,
        where=where,
        include=["documents", "metadatas", "distances"]
    )
    docs, metas, dists = resp["documents"][0], resp["metadatas"][0], resp["distances"][0]

    # 5) Collapse to best‐chunk per case_id
    best = {}
    for doc, md, dist in zip(docs, metas, dists):
        cid = md["case_id"]
        if cid not in best or dist < best[cid][2]:
            best[cid] = (doc, md, dist)

    sorted_hits = sorted(best.values(), key=lambda x: x[2])
    if not sorted_hits:
        return logs, "", "No matching cases after filters."

    # 6) If only one, return full narrative
    if len(sorted_hits) == 1:
        _, md, _ = sorted_hits[0]
        full = next(c for c in getCases() if c["case_id"] == md["case_id"])
        o = date.fromisoformat(full["metadata"]["date"]).toordinal()
        md_f = {**full["metadata"], "_ord": o}
        retrieved = f"- {full['case_id']}: {full['text']}  |  meta: {fmt_meta(md_f)}"
        llm_prompt = (
            f"You are an expert wildlife‐case analyst.  "
            f"Use ONLY the following case excerpts to answer the question.\n\n"
            f"Question: {query}\n\n"
            f"Excerpts:\n{retrieved}"
        )
        answer = call_llm(
            api_key=api_key,
            system="You are a helpful assistant who answers based on provided context.",
            user=llm_prompt
        )
        return logs, retrieved, answer

    # 7) Otherwise, bullet‐list **every** hit in relevance order
    bullets = []
    for doc, md, dist in sorted_hits:
        full = next(c for c in getCases() if c["case_id"] == md["case_id"])
        o = date.fromisoformat(full["metadata"]["date"]).toordinal()
        md_f = {**full["metadata"], "_ord": o}
        bullets.append(f"- {full['case_id']}: {full['text']}  |  meta: {fmt_meta(md_f)}")

    retrieved = "\n".join(bullets)

    llm_prompt = (
        f"You are an expert wildlife‐case analyst.  "
        f"Use ONLY the following case excerpts to answer the question.\n\n"
        f"Question: {query}\n\n"
        f"Excerpts:\n{retrieved}"
    )

    answer = call_llm(
        api_key=api_key,
        system="You are a helpful assistant who answers based on provided context.",
        user=llm_prompt
    )

    return logs, retrieved, answer
