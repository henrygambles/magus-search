# Magus Search

Magus Search is a small, end-to-end search engine for magic, esoterica, and miracle texts. It includes a sample corpus, a FastAPI backend, a Next.js UI, and an optional harvesting pipeline.

## Features
- FastAPI search API over a small local corpus.
- Next.js + Tailwind UI with facets and citations.
- Rights-aware harvesting pipeline (configurable sources).
- Optional OpenSearch + Qdrant via Docker Compose.

## Prerequisites
- Python 3
- Node.js + npm (for the frontend)
- Optional: Docker (for OpenSearch/Qdrant)
- Optional for OCR: `tesseract`, `pdftoppm` (Poppler)

## Quickstart (local dev)
Run both backend and frontend in one command:
```bash
bash run_dev.sh
# or
make dev
```

Open:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000

Try queries like `venus friday copper` or `lourdes testimony`.

### Run manually
Backend:
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

Frontend (separate terminal):
```bash
cd frontend
npm install
npm run dev
```

## Data
- Sample corpus: `data/sample_corpus.json`
- Harvested metadata: `data/harvested.jsonl`

## Harvesting pipeline
Configured sources live in `config/sources.yaml` and pipeline defaults in `config/pipeline.yaml`.

Run the full pipeline:
```bash
bash pipeline/cron_example.sh
# or
python pipeline/run_all.py
```

Run individual steps:
```bash
python pipeline/run_harvest.py
python pipeline/run_download.py
```

Required Python deps for the pipeline:
```bash
pip install requests pyyaml pypdf
```

OCR dependencies (optional):
```bash
# macOS
brew install tesseract poppler

# Ubuntu/Debian
sudo apt-get install tesseract-ocr poppler-utils
```

## Optional infrastructure
Start OpenSearch and Qdrant:
```bash
docker compose up -d
```

## Project structure
```
.
├─ backend/            # FastAPI app and search logic
├─ frontend/           # Next.js UI
├─ data/               # Sample corpus + harvested metadata
├─ config/             # Pipeline configuration
├─ harvesters/         # Source-specific harvesters
├─ pipeline/           # Harvesting + download pipeline
├─ docker-compose.yml  # Optional OpenSearch/Qdrant
├─ run_dev.sh          # One-command dev server
└─ install_dependencies.sh
```

## Ethics and safety
- Cite sources and label epistemic status (e.g., anecdote, scholarly, ecclesial).
- Avoid hazardous or medical guidance; present materials with appropriate disclaimers.

## Troubleshooting
macOS: if Next.js starts very slowly and logs SWC warnings, run:
```bash
bash fix_macos_swc.sh
# or from frontend/
npm run postinstall
```

## Testing
No automated tests are included yet.

## Contributing
Open an issue to discuss changes before sending a PR.

## License
No license file is present. Add a `LICENSE` to clarify usage.
