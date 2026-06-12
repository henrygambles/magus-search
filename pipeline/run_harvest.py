import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Ensure project root on sys.path for 'harvesters' imports
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

BASE = Path(__file__).resolve().parent.parent
DATA_OUT = BASE / "data" / "harvested.jsonl"
SOURCES = BASE / "config" / "sources.yaml"


class ProgressReporter:
    """Lightweight progress printer for console feedback."""

    def __init__(self, label: str, total: Optional[int] = None, width: int = 24) -> None:
        self.label = label
        self.total = total if total and total > 0 else None
        self.width = width
        self.count = 0
        self._last_len = 0
        self._had_updates = False

    def increment(self, step: int = 1) -> None:
        self.count += step
        self._had_updates = True
        self._emit(final=False)

    def finish(self, status: str = "complete") -> None:
        if not self._had_updates:
            message = f"{self.label}: no results"
        else:
            message = self._format(final=True)
        if status:
            message = f"{message} - {status}"
        self._write(message, final=True)

    def _format(self, final: bool = False) -> str:
        if self.total:
            ratio = min(1.0, self.count / self.total) if self.total else 0.0
            if final:
                ratio = 1.0
            pct = int(ratio * 100)
            filled = int(self.width * ratio)
            bar = "#" * filled + "-" * (self.width - filled)
            return f"{self.label} [{bar}] {pct:3d}% ({self.count}/{self.total})"
        return f"{self.label}: processed {self.count} items"

    def _emit(self, final: bool) -> None:
        message = self._format(final=final)
        self._write(message, final=final)

    def _write(self, message: str, final: bool) -> None:
        padding = max(0, self._last_len - len(message))
        sys.stdout.write("\r" + message + " " * padding)
        if final:
            sys.stdout.write("\n")
            self._last_len = 0
        else:
            self._last_len = len(message)
        sys.stdout.flush()


def norm_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text


def make_chunk(text: str, max_chars: int = 1200) -> List[Dict[str, Any]]:
    out = []
    for i in range(0, len(text), max_chars):
        ch = text[i : i + max_chars]
        out.append(
            {
                "id": f"ch-{i // max_chars}",
                "text": ch,
                "token_count": len(ch.split()),
                "page": None,
            }
        )
    return out


def load_seen_ids(path: Path) -> set[str]:
    seen: set[str] = set()
    if not path.exists():
        return seen
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                doc = json.loads(line)
                doc_id = doc.get("id")
                if doc_id:
                    seen.add(doc_id)
            except Exception:
                continue
    return seen


def write_doc(doc: Dict[str, Any], sink: Path, seen: set[str]) -> bool:
    doc_id = doc.get("id")
    if not doc_id or doc_id in seen:
        return False
    with sink.open("a", encoding="utf-8") as f:
        f.write(json.dumps(doc, ensure_ascii=False) + "\n")
    seen.add(doc_id)
    return True


def main() -> None:
    cfg = yaml.safe_load(SOURCES.read_text())
    allow = set(cfg["license_policy"]["allow"])
    block = set(cfg["license_policy"]["block"])
    DATA_OUT.parent.mkdir(parents=True, exist_ok=True)
    total_written = 0
    seen_ids = load_seen_ids(DATA_OUT)

    # Internet Archive
    from harvesters.internet_archive import fetch_items as ia_fetch

    for src in cfg["sources"]:
        if src["driver"] != "internet_archive":
            continue
        print(f"\n[internet_archive] {src['name']}")
        print(f"  query: {src['query']}")
        collections = src.get("collections")
        if collections:
            print(f"  collections: {', '.join(collections)}")
        max_items = src.get("max_items", 100)
        progress = ProgressReporter(f"{src['name']} (internet_archive)", max_items)
        saved = 0
        error: Optional[Exception] = None
        try:
            for item in ia_fetch(src["query"], collections, max_items):
                progress.increment()
                rights = (item.get("rights") or "").lower()
                license_label = (
                    "public_domain"
                    if "public domain" in rights or "pd" in rights
                    else ("unknown" if not rights else rights)
                )
                if license_label in block:
                    continue
                if license_label not in allow and not src.get("allow_unknown", False):
                    continue
                doc = {
                    "id": f"ia::{item['identifier']}",
                    "title": item["title"],
                    "author": item.get("creator", ""),
                    "date": item.get("date", ""),
                    "tradition": [],
                    "era": "",
                    "genre": "Scan",
                    "tags": ["internet_archive"],
                    "citation": {
                        "source": "Internet Archive",
                        "url": item["source"],
                        "license": license_label,
                    },
                    "text": "",
                    "chunks": [],
                    "extra": {"text_url": item.get("text_url")},
                }
                if write_doc(doc, DATA_OUT, seen_ids):
                    total_written += 1
                    saved += 1
        except Exception as exc:  # noqa: BLE001
            error = exc
        finally:
            progress.finish("error" if error else "complete")
        print(f"  processed: {progress.count} items; saved: {saved}")
        if error:
            print(f"  error: {error}")
            continue

    # Wikisource (metadata-only; text later)
    from harvesters.wikisource import search_terms as ws_search

    for src in cfg["sources"]:
        if src["driver"] != "wikisource":
            continue
        print(f"\n[wikisource] {src['name']}")
        print(f"  terms: {', '.join(src['search_terms'])}")
        print(f"  languages: {', '.join(src['languages'])}")
        max_items = src.get("max_items")
        progress = ProgressReporter(f"{src['name']} (wikisource)", max_items)
        saved = 0
        error: Optional[Exception] = None
        try:
            for res in ws_search(src["search_terms"], src["languages"]):
                progress.increment()
                doc = {
                    "id": f"wikisource::{res['lang']}::{res['pageid']}",
                    "title": res["title"],
                    "author": "",
                    "date": "",
                    "tradition": [],
                    "era": "",
                    "genre": "Primary Text",
                    "tags": ["wikisource"],
                    "citation": {
                        "source": "Wikisource",
                        "url": res["url"],
                        "license": "public_domain",
                    },
                    "text": "",
                    "chunks": [],
                    "extra": {"text_url": None},
                }
                if write_doc(doc, DATA_OUT, seen_ids):
                    total_written += 1
                    saved += 1
                if max_items and progress.count >= max_items:
                    break
        except Exception as exc:  # noqa: BLE001
            error = exc
        finally:
            progress.finish("error" if error else "complete")
        print(f"  processed: {progress.count} items; saved: {saved}")
        if error:
            print(f"  error: {error}")
            continue

    # Gallica SRU metadata
    from harvesters.gallica_oai import search_subject as gal_search

    for src in cfg["sources"]:
        if src["driver"] != "gallica_oai":
            continue
        print(f"\n[gallica_oai] {src['name']}")
        print(f"  subject contains: {', '.join(src['subject_contains'])}")
        print(f"  date before: {src['date_before']}")
        max_items = src.get("max_items", 100)
        progress = ProgressReporter(f"{src['name']} (gallica_oai)", max_items)
        saved = 0
        error: Optional[Exception] = None
        try:
            for rec in gal_search(src["subject_contains"], src["date_before"], max_items):
                progress.increment()
                doc = {
                    "id": f"gallica::{rec['ark']}",
                    "title": rec["ark"],
                    "author": "",
                    "date": "",
                    "tradition": [],
                    "era": "",
                    "genre": "Scan",
                    "tags": ["gallica"],
                    "citation": {
                        "source": "BnF Gallica",
                        "url": rec["source"],
                        "license": "public_domain",
                    },
                    "text": "",
                    "chunks": [],
                    "extra": {"text_url": rec.get("text_url")},
                }
                if write_doc(doc, DATA_OUT, seen_ids):
                    total_written += 1
                    saved += 1
        except Exception as exc:  # noqa: BLE001
            error = exc
        finally:
            progress.finish("error" if error else "complete")
        print(f"  processed: {progress.count} items; saved: {saved}")
        if error:
            print(f"  error: {error}")
            continue

    # Wellcome Collection metadata
    from harvesters.wellcome import search as well_search

    for src in cfg["sources"]:
        if src["driver"] != "wellcome":
            continue
        print(f"\n[wellcome] {src['name']}")
        print(f"  query: {src['q']}")
        print(f"  date before: {src['date_before']}")
        max_items = src.get("max_items", 100)
        progress = ProgressReporter(f"{src['name']} (wellcome)", max_items)
        saved = 0
        error: Optional[Exception] = None
        try:
            for rec in well_search(
                src["q"],
                src["date_before"],
                src.get("work_types"),
                max_items=max_items,
            ):
                progress.increment()
                doc = {
                    "id": f"wellcome::{rec['id']}",
                    "title": rec["title"],
                    "author": "",
                    "date": str(rec.get("year", "")),
                    "tradition": [],
                    "era": "",
                    "genre": "Scan",
                    "tags": ["wellcome"],
                    "citation": {
                        "source": "Wellcome Collection",
                        "url": rec["source"],
                        "license": "public_domain",
                    },
                    "text": "",
                    "chunks": [],
                    "extra": {"text_url": rec.get("text_url")},
                }
                if write_doc(doc, DATA_OUT, seen_ids):
                    total_written += 1
                    saved += 1
        except Exception as exc:  # noqa: BLE001
            error = exc
        finally:
            progress.finish("error" if error else "complete")
        print(f"  processed: {progress.count} items; saved: {saved}")
        if error:
            print(f"  error: {error}")
            continue

    # DOAJ + Crossref + Unpaywall (modern scholarship triage)
    from harvesters.doaj_crossref_unpaywall import (
        crossref_licenses,
        doaj_articles,
        unpaywall_status,
    )

    email = os.environ.get("UNPAYWALL_EMAIL", "example@example.com")
    for src in cfg["sources"]:
        if src["driver"] != "doaj_crossref_unpaywall":
            continue
        print(f"\n[doaj_crossref_unpaywall] {src['name']}")
        print(f"  query: {src['q']}")
        max_items = src.get("max_items", 100)
        progress = ProgressReporter(f"{src['name']} (doaj)", max_items)
        saved = 0
        error: Optional[Exception] = None
        try:
            for art in doaj_articles(src["q"], max_items):
                progress.increment()
                lic = crossref_licenses(art.get("doi"))
                upw = unpaywall_status(art["doi"], email) if art.get("doi") else {}
                status = (upw.get("oa_status") or "unknown").lower()
                if status in block:
                    continue
                doc = {
                    "id": f"doaj::{art.get('doi') or art['title'][:50]}",
                    "title": art["title"],
                    "author": "",
                    "date": "",
                    "tradition": [],
                    "era": "Contemporary",
                    "genre": "Scholarly",
                    "tags": ["doaj"],
                    "citation": {
                        "source": "DOAJ/Crossref/Unpaywall",
                        "url": "",
                        "license": lic.get("license"),
                    },
                    "text": "",
                    "chunks": [],
                    "extra": {
                        "text_url": (upw.get("best_oa_location") or {}).get("url")
                    },
                }
                if write_doc(doc, DATA_OUT, seen_ids):
                    total_written += 1
                    saved += 1
        except Exception as exc:  # noqa: BLE001
            error = exc
        finally:
            progress.finish("error" if error else "complete")
        print(f"  processed: {progress.count} items; saved: {saved}")
        if error:
            print(f"  error: {error}")
            continue

    print(f"\nHarvest complete. Wrote {total_written} records to {DATA_OUT}")


if __name__ == "__main__":
    main()
