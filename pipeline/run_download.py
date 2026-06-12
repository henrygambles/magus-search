import os, json, re, shutil, subprocess, tempfile
from pathlib import Path
from typing import Dict, Any
import requests
import yaml

import sys, pathlib
# Ensure project root on sys.path for 'harvesters' imports
_PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
BASE = Path(__file__).resolve().parent.parent
CFG = yaml.safe_load((BASE / "config" / "pipeline.yaml").read_text())
HARVESTED = BASE / "data" / "harvested.jsonl"
CORPUS_OUT = BASE / "data" / "corpus.jsonl"
DL_DIR = BASE / CFG.get("downloads_dir", "downloads")
DELETE_AFTER = bool(CFG.get("delete_downloads_after", True))
CHUNK_MAX = int(CFG.get("chunk_max_chars", 1200))
LIMIT = int(CFG.get("max_docs_per_run", 200))

def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text

def chunk(text: str, max_chars: int):
    for i in range(0, len(text), max_chars):
        yield text[i:i+max_chars], i//max_chars

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

def write_doc(doc: Dict[str, Any], seen: set[str]) -> bool:
    doc_id = doc.get("id")
    if not doc_id or doc_id in seen:
        return False
    with CORPUS_OUT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(doc, ensure_ascii=False) + "\n")
    seen.add(doc_id)
    return True

def ocr_pdf_to_text(pdf_path: Path) -> str:
    # Requires: tesseract + (optionally) pdftoppm (poppler) or imagemagick
    # We attempt pdftoppm -> tesseract per page (most robust).
    out_texts = []
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        # Convert PDF to images
        try:
            # pdftoppm -r 300 in.pdf out
            subprocess.run(["pdftoppm", "-r", "300", str(pdf_path), str(td_path / "page")], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            imgs = sorted(td_path.glob("page-*.ppm"))
            if not imgs:
                # Newer pdftoppm names: page-1.png if -png
                subprocess.run(["pdftoppm", "-png", "-r", "300", str(pdf_path), str(td_path / "page")], check=True)
                imgs = sorted(td_path.glob("page-*.png"))
        except Exception as e:
            return ""  # Skip if no poppler
        for img in imgs:
            txt_file = img.with_suffix(".txt")
            try:
                subprocess.run(["tesseract", str(img), str(img.with_suffix("")), "-l", "eng"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if txt_file.exists():
                    out_texts.append(txt_file.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                continue
    return "\n".join(out_texts)

def download_text(url: str, dest: Path) -> Path|None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(url, timeout=60)
    if r.status_code != 200:
        return None
    dest.write_bytes(r.content)
    return dest

def extract_text(file_path: Path) -> str:
    # Simple extractor: .txt direct; .pdf try naive text, else OCR
    if file_path.suffix.lower() == ".txt":
        return file_path.read_text(encoding="utf-8", errors="ignore")
    if file_path.suffix.lower() == ".pdf":
        # Try PyPDF text extraction if available
        try:
            import pypdf
            reader = pypdf.PdfReader(str(file_path))
            text = "\n".join([p.extract_text() or "" for p in reader.pages])
            if text and len(text.strip()) > 100:
                return text
        except Exception:
            pass
        # Fallback to OCR
        return ocr_pdf_to_text(file_path)
    return ""

def main():
    if not HARVESTED.exists():
        print("No harvested.jsonl found. Run pipeline/run_harvest.py first.")
        return
    processed = 0
    seen_corpus = load_seen_ids(CORPUS_OUT)
    seen_this_run: set[str] = set()
    with HARVESTED.open("r", encoding="utf-8") as f:
        for line in f:
            if processed >= LIMIT:
                break
            try:
                meta = json.loads(line)
            except json.JSONDecodeError:
                continue
            meta_id = meta.get("id")
            if not meta_id or meta_id in seen_corpus or meta_id in seen_this_run:
                continue
            text_url = (meta.get("extra") or {}).get("text_url")
            if not text_url:
                # Skip for now; extend later with IIIF/PDF resolution per source
                continue
            # Decide filename
            ident = re.sub(r"[^a-zA-Z0-9_.-]+", "_", meta["id"])
            ext = ".txt" if text_url.endswith(".txt") else ".pdf"
            dest = DL_DIR / f"{ident}{ext}"
            fp = download_text(text_url, dest)
            if not fp:
                continue
            raw = extract_text(fp)
            if DELETE_AFTER and fp.exists():
                try:
                    fp.unlink()
                except Exception:
                    pass
            text = clean_text(raw)
            if not text or len(text) < 500:
                continue
            chunks = []
            for ch, idx in chunk(text, CHUNK_MAX):
                chunks.append({"id": f"{meta['id']}-ch{idx}", "text": ch, "token_count": len(ch.split()), "page": None})
            out = {
                "id": meta["id"],
                "title": meta.get("title",""),
                "author": meta.get("author",""),
                "date": meta.get("date",""),
                "tradition": meta.get("tradition", []),
                "era": meta.get("era", ""),
                "genre": meta.get("genre", ""),
                "tags": meta.get("tags", []),
                "citation": meta.get("citation", {}),
                "text": text[:500] + ("..." if len(text) > 500 else ""),
                "chunks": chunks
            }
            if write_doc(out, seen_corpus):
                seen_this_run.add(meta_id)
                processed += 1
                print(f"Processed {processed}: {meta.get('title')}")
    print(f"Wrote {CORPUS_OUT} with {processed} documents")

if __name__ == "__main__":
    main()
