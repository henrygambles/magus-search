from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from .search_core import rank, corpus_stats

app = FastAPI(title="Magus Search (MVP)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

class SearchFilters(BaseModel):
    tradition: Optional[List[str]] = None
    era: Optional[List[str]] = None
    genre: Optional[List[str]] = None

@app.get("/health")
def health():
    return {"ok": True, **corpus_stats()}

@app.get("/search")
def search(q: str = "", tradition: str = "", era: str = "", genre: str = ""):
    filters: Dict[str, List[str]] = {}
    if tradition:
        filters["tradition"] = tradition.split(",")
    if era:
        filters["era"] = era.split(",")
    if genre:
        filters["genre"] = genre.split(",")
    results = rank(q, filters if filters else None)
    # Simple scholar note (stub) + citations
    return {
        "query": q,
        "count": len(results),
        "results": results
    }
