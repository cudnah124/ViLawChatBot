import json
from datetime import datetime
from rank_bm25 import BM25Okapi
from underthesea import word_tokenize
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from app.services.llm_engine import get_llm
from app.services.blockchain import BlockchainService
from app.db.session import SessionLocal
from app.db.models import LawChunk, ChatHistory

class RAGService:
    _instance = None
    _bm25 = None
    _doc_texts = None
    _llm = None
    
    # Định nghĩa System Prompt là hằng số để dễ quản lý, tránh viết lặp lại
    SYSTEM_PROMPT = """
    <|im_start|>system
    Bạn là ViLaw, trợ lý pháp lý. Chỉ trả lời các câu hỏi liên quan đến pháp luật tại Việt Nam.
    Nếu người dùng hỏi về lập trình, code, công nghệ, hoặc phi pháp, hãy từ chối lịch sự.
    Đặc biệt, với câu hỏi về hợp đồng/quyền/nghĩa vụ, trả lời theo cấu trúc 3 phần:
    1. Quyền lợi: ...
    2. Nghĩa vụ: ...
    3. Rủi ro: ...
    Ngữ cảnh:
    {context}
    <|im_end|>
    """

    def __new__(cls):
        # Singleton Pattern: Chỉ khởi tạo 1 lần duy nhất
        if cls._instance is None:
            cls._instance = super(RAGService, cls).__new__(cls)
            # cls._init_resources()
        return cls._instance

    @classmethod
    def _init_resources(cls):
        """Hàm này chỉ chạy 1 lần khi server khởi động"""
        print("--- RAGService: Initializing Resources... ---")


        db = SessionLocal()
        try:
            laws = db.query(LawChunk).filter(LawChunk.content != None).all()
            cls._doc_texts = [law.content for law in laws if law.content and law.content.strip()]
        finally:
            db.close()

        if not cls._doc_texts:
            cls._doc_texts = ["Không có dữ liệu pháp luật trong database."]

        # Tokenize & Build BM25
        # Lưu ý: corpus_tokenized không cần lưu vào class attribute nếu chỉ dùng để build bm25
        corpus_tokenized = [word_tokenize(doc, format="text").split() for doc in cls._doc_texts]
        cls._bm25 = BM25Okapi(corpus_tokenized)
        
        # Init LLM
        cls._llm = get_llm(streaming=True)
        print("--- RAGService: Ready ---")

    def retrieve(self, query, k=3):
        # Sửa lỗi: Dùng self._bm25 thay vì self.bm25
        query_tok = word_tokenize(query, format="text").split()
        scores = self._bm25.get_scores(query_tok)
        top_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        return [self._doc_texts[i] for i in top_idx]

    def _create_prompt(self, history_str):
        """Hàm helper để ghép prompt động"""
        full_template = f"""
{self.SYSTEM_PROMPT}
{history_str}
<|im_start|>user
Câu hỏi: {{question}}
<|im_end|>
<|im_start|>assistant
"""
        return ChatPromptTemplate.from_template(full_template)

    @classmethod
    def refresh_knowledge(cls):
        """Public method to refresh/reload RAG resources (rebuild BM25, reload chunks)."""
        try:
            cls._init_resources()
            print("RAGService: Knowledge refreshed.")
        except Exception as e:
            print(f"RAGService.refresh_knowledge error: {e}")

    async def chat_stream(self, message: str, conversation_id: str = '1', db=None):
        # Logic quản lý DB Session
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
            
        history_str = ""
        try:
            # Try to use a Message model if it exists; otherwise skip memory loading
            Message = None
            try:
                from app.db.models import Message as _Message
                Message = _Message
            except Exception:
                Message = None

            if Message:
                mem_msg = db.query(Message).filter(Message.conversation_id == conversation_id, Message.role == 'memory').first()
                if mem_msg and getattr(mem_msg, 'content', None):
                    try:
                        history = json.loads(mem_msg.content)
                        for turn in history:
                            role = turn.get('role')
                            content = turn.get('content', '')
                            if role in ['user', 'assistant']:
                                history_str += f"<|im_start|>{role}\n{content}<|im_end|>\n"
                    except Exception:
                        pass
        finally:
            if close_db:
                db.close()

        # Ensure resources are initialized (BM25, docs, LLM)
        if not getattr(self, '_bm25', None):
            try:
                type(self)._init_resources()
            except Exception as e:
                print(f"RAGService: failed to init resources: {e}")

        # 1. Retrieve Context
        context = "\n\n".join(self.retrieve(message, k=3))
        
        # 2. Create Chain (Tái sử dụng prompt template gọn gàng hơn)
        prompt_template = self._create_prompt(history_str)
        
        chain = (
            {"context": lambda _: context, "question": RunnablePassthrough()}
            | prompt_template
            | self._llm
            | StrOutputParser()
        )

        # 3. Streaming & Blockchain
        full_response = ""
        async for chunk in chain.astream(message):
            full_response += chunk
            yield chunk
            
        tx_hash, timestamp = BlockchainService.create_hash(full_response)
        yield f"\n\n[🛡️ HASH: {tx_hash} | TIMESTAMP: {timestamp}]"