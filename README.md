# ViLaw - Legal AI Assistant

A RAG-based legal assistant for Vietnamese legislation analysis.

## Overview

ViLaw provides context-aware retrieval and analysis of Vietnamese legal documents using BM25 lexical search combined with LLM-powered responses. The system processes 1,000+ official legal documents with Vietnamese word segmentation for accurate query matching.

## Tech Stack

- **Backend**: Python, FastAPI
- **NLP**: LangChain, underthesea (Vietnamese tokenizer)
- **Search**: BM25 (rank_bm25)
- **Database**: SQLite / PostgreSQL
- **LLM**: OpenRouter API

## Features

- Legal Q&A with contextual retrieval
- Contract risk analysis
- Legal procedure guidance
- Document OCR processing
- Admin dashboard for knowledge base management

## Project Structure

```
vilaw_backend/
├── app/
│   ├── api/v1/          # API endpoints
│   ├── core/            # Configuration
│   ├── db/              # Database models
│   ├── schemas/         # Pydantic schemas
│   └── services/        # Business logic (RAG, OCR, etc.)
├── static/              # Uploaded documents
└── main.py              # Application entry point
```

## Setup

```bash
cd vilaw_backend
pip install -r requirements.txt
```

Create `.env` file:
```
DATABASE_URL=sqlite:///./vilaw_db.sqlite3
OPENROUTER_API_KEY=your_api_key
OPENROUTER_MODEL=google/gemini-flash-1.5
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

## Run

```bash
python main.py
```

API available at `http://localhost:8000`

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/chat` | Legal Q&A |
| `POST /api/v1/contracts/analyze` | Contract risk analysis |
| `POST /api/v1/procedures` | Procedure guidance |
| `POST /api/v1/db/upload` | Upload legal documents |

## License

MIT