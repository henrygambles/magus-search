import requests, time
from typing import Iterator, Dict

DOAJ = "https://doaj.org/api/v2/search/articles/{q}?page={page}"
CROSSREF = "https://api.crossref.org/works"
UNPAYWALL = "https://api.unpaywall.org/v2/{doi}?email={email}"

def doaj_articles(q:str, max_items:int=200) -> Iterator[Dict]:
    page = 1; fetched = 0
    while fetched < max_items:
        r = requests.get(DOAJ.format(q=q, page=page), timeout=30)
        if r.status_code != 200: break
        data = r.json()
        results = data.get("results", [])
        if not results: break
        for res in results:
            bib = res.get("bibjson", {})
            doi = None
            for iden in bib.get("identifier", []):
                if iden.get("type") == "doi":
                    doi = iden.get("id")
            yield {"title": bib.get("title"), "doi": doi, "journal": bib.get("journal", {}).get("title")}
            fetched += 1
            if fetched >= max_items: break
        page += 1
        time.sleep(0.5)

def crossref_licenses(doi:str|None) -> Dict:
    if not doi: return {}
    r = requests.get(CROSSREF, params={"filter": f"doi:{doi}"}, timeout=20)
    if r.status_code != 200: return {}
    items = r.json().get("message", {}).get("items", [])
    if not items: return {}
    item = items[0]
    lic = item.get("license", [])
    return {"license": lic[0]["URL"] if lic else None}

def unpaywall_status(doi:str, email:str) -> Dict:
    r = requests.get(UNPAYWALL.format(doi=doi, email=email), timeout=20)
    if r.status_code != 200: return {}
    data = r.json()
    return {"oa_status": data.get("oa_status"), "best_oa_location": data.get("best_oa_location")}
