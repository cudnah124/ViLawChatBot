from pydantic import BaseModel

class ChatRequest(BaseModel):
    question: str
    # Có thể mở rộng thêm: conversation_id, user_id...