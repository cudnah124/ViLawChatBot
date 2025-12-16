# Copilot Instructions for ViLawChatBot

## Project Overview
ViLawChatBot is a legal AI assistant platform with the following core features:
- **Legal Q&A Chatbot**: Natural language legal consultation, streaming answers via `/api/v1/chat/stream`.
- **Smart Contract Drafting**: Dynamic contract/document generation, not static templates, via `/api/v1/contracts/draft`.
- **Risk Checker**: Automated contract/document risk analysis via `/api/v1/contracts/check-risk`.
- **Document Analysis**: OCR and legal annotation for uploaded files.
- **Procedural Guidance**: Step-by-step administrative process and checklist support.

## Architecture & Key Patterns
- **Backend**: Python (FastAPI), organized by domain in `vilaw_backend/app/`:
  - `api/v1/`: API endpoints (chat, contracts, documents, procedures, upload)
  - `services/`: Core business logic (RAG, LLM, drafting, risk checking, blockchain, OCR)
  - `schemas/`: Pydantic models for request/response validation
  - `core/`: Config, security, and exception handling
  - `db/`: Vector store and DB session management
- **Vector Search**: Uses Pinecone and custom Vietnamese SBERT embeddings (see `rag_service.py`).
- **LLM Integration**: All LLM calls are abstracted via `llm_engine.py`.
- **Blockchain**: Hashes for document authenticity are managed in `blockchain.py`.
- **Static Files**: Generated docs are saved in `/static/docs` and served via `/static`.

## Developer Workflows
- **Run API Locally**: `python vilaw_backend/main.py` or use Uvicorn for hot reload.
- **Dependencies**: Managed in `vilaw_backend/requirements.txt`.
- **Testing**: (If present) See `test_checklist.py` for test entry points.
- **API Reference**: See `vilaw_backend/README_API_FRONTEND.md` for endpoint details and payloads.

## Project-Specific Conventions
- **Prompt Engineering**: Prompts are defined in code (see `drafter.py`), not in external files.
- **Streaming Responses**: Chat endpoint streams results using FastAPI's `StreamingResponse`.
- **Error Handling**: API returns HTTP 500 with generic messages for system errors.
- **Vietnamese Language**: All prompts, responses, and legal logic are tailored for Vietnamese law and language.
- **File Structure**: All new features should be added as a new service in `services/` and exposed via a router in `api/v1/`.

## Integration Points
- **Frontend**: Communicates via REST API (see `README_API_FRONTEND.md`).
- **External Services**: Pinecone (vector DB), HuggingFace/Transformers, Blockchain (for document hashes).

## Examples
- To add a new legal feature: create a service in `services/`, define schemas, and expose via a new router in `api/v1/`.
- To update embeddings: modify `VietnameseSBERTEmbeddings` in `rag_service.py`.

---
For more details, see the main `README.md` and `vilaw_backend/README_API_FRONTEND.md`.
