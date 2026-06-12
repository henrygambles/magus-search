import json, uuid, re
from pathlib import Path

def chunk_text(text: str, max_chars: int = 1200):
    chunks = []
    for i in range(0, len(text), max_chars):
        chunks.append(text[i:i+max_chars])
    return chunks

def build_doc(path: Path, meta: dict):
    text = path.read_text(encoding='utf-8', errors='ignore')
    chs = chunk_text(text)
    return {
        "id": meta.get("id", path.stem),
        "title": meta.get("title", path.stem),
        "author": meta.get("author", "Unknown"),
        "date": meta.get("date", ""),
        "tradition": meta.get("tradition", []),
        "era": meta.get("era", ""),
        "genre": meta.get("genre", "Unknown"),
        "tags": meta.get("tags", []),
        "citation": meta.get("citation", {}),
        "text": text[:500] + ("..." if len(text) > 500 else ""),
        "chunks": [
            {"id": f"{path.stem}-{i}", "text": ch, "token_count": len(ch.split()), "page": None}
            for i, ch in enumerate(chs)
        ]
    }

def main():
    # Example usage: place raw .txt files in ./raw and add metadata in code here.
    raw_dir = Path(__file__).parent / "raw"
    out_path = Path(__file__).parent.parent / "data" / "sample_corpus.json"
    docs = []
    for txt in raw_dir.glob("*.txt"):
        meta = {"id": txt.stem, "title": txt.stem}
        docs.append(build_doc(txt, meta))
    out_path.write_text(json.dumps(docs, indent=2), encoding='utf-8')
    print(f"Wrote {out_path} with {len(docs)} docs")

if __name__ == "__main__":
    main()
