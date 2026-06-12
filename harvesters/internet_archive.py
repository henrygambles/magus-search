import requests, time, json
from typing import Iterator, Dict

SEARCH = "https://archive.org/advancedsearch.php"
METADATA = "https://archive.org/metadata/{identifier}"
DOWNLOAD = "https://archive.org/download/{identifier}/{file}"

def _search(query: str, collections: list[str]|None=None, max_items=100) -> Iterator[Dict]:
    page = 1
    fetched = 0
    clause = query
    if collections:
        col_q = " OR ".join([f'collection:{c}' for c in collections])
        clause = f"({query}) AND ({col_q})"
    params = {"q": clause, "output": "json", "rows": 100, "page": page}
    while fetched < max_items:
        r = requests.get(SEARCH, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        docs = data.get("response", {}).get("docs", [])
        if not docs:
            break
        for d in docs:
            yield d
            fetched += 1
            if fetched >= max_items:
                break
        page += 1
        params["page"] = page
        time.sleep(0.5)

def fetch_items(query, collections=None, max_items=100):
    for doc in _search(query, collections, max_items):
        ident = doc.get("identifier")
        if not ident: 
            continue
        meta = requests.get(METADATA.format(identifier=ident), timeout=30).json()
        files = meta.get("files", [])
        # Prefer OCR text files
        text_file = next((f["name"] for f in files if f.get("name","").endswith("_text.pdf") or f.get("name","").endswith(".txt")), None)
        rights = meta.get("metadata", {}).get("licenseurl") or meta.get("metadata", {}).get("rights") or ""
        yield {
            "identifier": ident,
            "title": meta.get("metadata", {}).get("title", ident),
            "creator": meta.get("metadata", {}).get("creator", ""),
            "date": meta.get("metadata", {}).get("date", ""),
            "rights": rights,
            "source": f"https://archive.org/details/{ident}",
            "text_url": DOWNLOAD.format(identifier=ident, file=text_file) if text_file else None
        }
