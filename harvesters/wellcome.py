import requests
from typing import Iterator, Dict

API = "https://api.wellcomecollection.org/catalogue/v2/works"

def search(q:str, before_year:int=1930, types:list[str]|None=None, page_size:int=50, max_items:int=100):
    page = 1
    fetched = 0
    params = {"pageSize": page_size, "query": q}
    # Filter for date using production.dates.from.year lte
    while fetched < max_items:
        r = requests.get(API, params=params, timeout=20)
        if r.status_code != 200: break
        data = r.json()
        for work in data.get("results", []):
            year = None
            if work.get("production") and work["production"].get("dates"):
                year = work["production"]["dates"][0].get("from", {}).get("year")
            if year and year > before_year:
                continue
            fetched += 1
            yield {
                "id": work.get("id"),
                "title": work.get("title"),
                "year": year,
                "source": f"https://wellcomecollection.org/works/{work.get('id')}"
            }
        if "nextPage" not in data:
            break
        params["page"] = data["nextPage"]
