import requests, re
from typing import Iterator, Dict

CORE = "https://api.wikimedia.org/core/v1/{project}/{lang}/search/page"

def search_terms(terms:list[str], langs:list[str]) -> Iterator[Dict]:
    for lang in langs:
        for q in terms:
            url = CORE.format(project="wikisource", lang=lang)
            r = requests.get(url, params={"q": q, "limit": 20}, timeout=20)
            if r.status_code != 200:
                continue
            data = r.json()
            for item in data.get("pages", []):
                title = item.get("title")
                pageid = item.get("id")
                yield {
                    "lang": lang,
                    "title": title,
                    "pageid": pageid,
                    "url": f"https://{lang}.wikisource.org/wiki/{title.replace(' ', '_')}"
                }
