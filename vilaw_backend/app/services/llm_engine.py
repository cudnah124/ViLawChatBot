from langchain_openai import ChatOpenAI
from app.core.config import settings

def get_llm(streaming: bool = False, temperature: float = 0.3):
    """
    Khởi tạo LLM kết nối tới OpenRouter.
    Có thể tái sử dụng cho nhiều service khác nhau.
    """
    llm = ChatOpenAI(
        model=settings.OPENROUTER_MODEL,
        openai_api_key=settings.OPENROUTER_API_KEY,
        openai_api_base=settings.OPENROUTER_BASE_URL,
        streaming=streaming,
        temperature=temperature,
        default_headers={
            "HTTP-Referer": "https://vilaw.vn",
            "X-Title": "ViLaw Backend"
        },
        max_tokens=1024
    )
    return llm