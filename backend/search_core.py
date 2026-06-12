import json, math, re, pathlib, logging
from typing import List, Dict, Any, Set

DATA_PATH = pathlib.Path(__file__).parent.parent / "data" / "sample_corpus.json"
logger = logging.getLogger(__name__)

def _load_corpus() -> tuple[List[Dict[str, Any]], List[pathlib.Path]]:
    """Load the corpus and de-duplicate by id (first-write wins)."""
    corpus_by_id: Dict[str, Dict[str, Any]] = {}
    sources: List[pathlib.Path] = []

    def add_doc(doc: Dict[str, Any]) -> None:
        doc_id = doc.get("id")
        if not doc_id or doc_id in corpus_by_id:
            return
        corpus_by_id[doc_id] = doc

    # Baseline sample corpus
    if DATA_PATH.exists():
        with DATA_PATH.open("r", encoding="utf-8") as f:
            for doc in json.load(f):
                add_doc(doc)
        sources.append(DATA_PATH)
    else:
        logger.warning("Sample corpus missing at %s", DATA_PATH)

    # Pipeline-built corpus (jsonl)
    corpus_jsonl = pathlib.Path(__file__).parent.parent / "data" / "corpus.jsonl"
    if corpus_jsonl.exists():
        for line in corpus_jsonl.open("r", encoding="utf-8"):
            try:
                add_doc(json.loads(line))
            except Exception:
                continue
        sources.append(corpus_jsonl)

    docs = list(corpus_by_id.values())
    if docs:
        logger.info("Loaded %s docs into corpus", len(docs))
    else:
        logger.warning(
            "Search corpus is empty. Ensure data/sample_corpus.json or data/corpus.jsonl exists."
        )
    return docs, sources


CORPUS: List[Dict[str, Any]]
CORPUS_SOURCES: List[pathlib.Path]
CORPUS, CORPUS_SOURCES = _load_corpus()

def corpus_stats() -> Dict[str, Any]:
    return {"docs": len(CORPUS), "sources": [str(p) for p in CORPUS_SOURCES]}

def tokenize(q: str):
    return re.findall(r"[a-z0-9]+", q.lower())

def keyword_score(text: str, terms: List[str]) -> float:
    if not terms:
        return 0.0
    t = text.lower()
    return sum(t.count(term) for term in terms) / (len(t.split()) + 1e-6)

def tag_boost(item: Dict[str, Any], terms: List[str]) -> float:
    tags = " ".join(item.get("tags", []) + item.get("tradition", [])).lower()
    return sum(1.0 for term in terms if term in tags) * 0.2

def rank(query: str, filters: Dict[str, List[str]] | None = None) -> List[Dict[str, Any]]:
    terms = tokenize(query)
    results = []
    seen_ids: Set[str] = set()
    for doc in CORPUS:
        # Filter
        if filters:
            ok = True
            for k, vals in filters.items():
                if vals and not any(v in doc.get(k, []) if isinstance(doc.get(k, []), list) else v == doc.get(k) for v in vals):
                    ok = False
                    break
            if not ok:
                continue
        doc_id = doc.get("id")
        if doc_id in seen_ids:
            continue
        # Score: best chunk + tag boost
        best_chunk = None
        best_chunk_score = 0.0
        chunks = doc.get("chunks") or []
        for ch in chunks:
            s = keyword_score(ch["text"], terms)
            if s > best_chunk_score:
                best_chunk_score = s
                best_chunk = ch
        # Fallback to unchunked text if present
        if not chunks and doc.get("text"):
            best_chunk_score = keyword_score(doc["text"], terms)
            if best_chunk_score > 0:
                best_chunk = {"text": doc["text"]}
        total = best_chunk_score + tag_boost(doc, terms)
        if total > 0 or not terms:
            results.append({
                "id": doc_id,
                "title": doc["title"],
                "author": doc["author"],
                "date": doc["date"],
                "tradition": doc.get("tradition", []),
                "era": doc.get("era", ""),
                "genre": doc.get("genre", ""),
                "tags": doc.get("tags", []),
                "citation": doc.get("citation", {}),
                "snippet": best_chunk["text"] if best_chunk else (doc.get("text","")[:200]),
                "score": round(float(total), 4)
            })
            seen_ids.add(doc_id)
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:20]
