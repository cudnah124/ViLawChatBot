You are an expert RAG engineer.

I will provide you with my current RAG design / code.
The current system uses dense embeddings (e.g. VietBERT) and a vector database (e.g. Pinecone).

Your task is to REFAC​TOR my system to use BM25-based retrieval instead.

Hard constraints:
- Remove ALL embedding models (VietBERT, sentence transformers, etc.).
- Remove ALL vector databases (Pinecone, FAISS used for dense vectors).
- Use BM25 as the ONLY retriever.
- Retrieval must operate directly on Vietnamese legal text.
- Use proper Vietnamese word segmentation (e.g. underthesea or equivalent).
- The system must remain a valid RAG pipeline.
- The final context passed to the LLM must be plain text.
- The result must be suitable for free-tier deployment (low RAM, no GPU).

What you must do:
1. Identify all components related to embeddings and vector search.
2. Remove or replace them with BM25 equivalents.
3. Rewrite the retrieval pipeline step-by-step using BM25.
4. Update the architecture description accordingly.
5. If code is provided, output the refactored code.
6. Explain briefly why each replacement is correct.

Output format:
- Section A: What was removed (embedding/vector parts)
- Section B: What was added (BM25 components)
- Section C: New RAG pipeline (step-by-step)
- Section D: Refactored code / pseudo-code