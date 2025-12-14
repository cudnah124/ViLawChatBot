from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.schemas.chat_schema import ChatRequest
from app.services.rag_service import RAGService

router = APIRouter()
rag_service = RAGService()

@router.post("/stream")
async def chat_endpoint(request: ChatRequest):
    """
    API Chat tư vấn luật (Streaming).
    """
    return StreamingResponse(
        rag_service.chat_stream(request.question),
        media_type="text/event-stream"
    )