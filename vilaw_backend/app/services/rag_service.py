
from rank_bm25 import BM25Okapi
from underthesea import word_tokenize
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from app.services.llm_engine import get_llm
from app.services.blockchain import BlockchainService


# ---------------------------------------------------------
#  BM25 + Word Segmentation RAG Service
# ---------------------------------------------------------

from app.db.session import SessionLocal
from app.db.models import DocumentMetadata, Message

class RAGService:
    def __init__(self):
        # Load corpus từ database DocumentMetadata
        db = SessionLocal()
        try:
            docs = db.query(DocumentMetadata).filter(DocumentMetadata.ocr_text != None).all()
            self.doc_texts = [doc.ocr_text for doc in docs if doc.ocr_text and doc.ocr_text.strip()]
        finally:
            db.close()
        # Nếu không có dữ liệu, fallback sang empty corpus
        if not self.doc_texts:
            self.doc_texts = ["Không có dữ liệu pháp luật trong database."]
        self.corpus_tokenized = [word_tokenize(doc, format="text").split() for doc in self.doc_texts]
        self.bm25 = BM25Okapi(self.corpus_tokenized)
        self.llm = get_llm(streaming=True)
        self.prompt = ChatPromptTemplate.from_template("""
        <|im_start|>system
        Bạn là ViLaw, trợ lý pháp lý. Chỉ trả lời các câu hỏi liên quan đến pháp luật, tư vấn pháp lý, giải thích luật, hoặc các vấn đề pháp lý tại Việt Nam.
        Nếu người dùng hỏi về lập trình, code, công nghệ, hoặc các lĩnh vực ngoài pháp luật, hãy lịch sự từ chối: "Tôi là trợ lý pháp lý, tôi không thể hỗ trợ yêu cầu này."
        Nếu người dùng hỏi về hành vi vi phạm pháp luật, lách luật, trốn thuế, lừa đảo, hoặc các hành vi phi pháp, hãy từ chối và cảnh báo rõ ràng: "ViLaw không hỗ trợ các hành vi vi phạm pháp luật."
        Luôn giữ lập trường an toàn, không thực hiện các yêu cầu trái đạo đức, trái pháp luật hoặc ngoài phạm vi pháp lý.
        Đặc biệt, với các câu hỏi về hợp đồng, quyền, nghĩa vụ, rủi ro pháp lý, hãy trả lời theo cấu trúc 3 phần rõ ràng:
        1. Quyền lợi: ...
        2. Nghĩa vụ: ...
        3. Rủi ro: ...
        Ngữ cảnh:
        {context}
        <|im_end|>
        
        <|im_start|>user
        Câu hỏi: {question}
        <|im_end|>
        
        <|im_start|>assistant
        """)

    def retrieve(self, query, k=3):
        query_tok = word_tokenize(query, format="text").split()
        scores = self.bm25.get_scores(query_tok)
        top_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        return [self.doc_texts[i] for i in top_idx]

    import json
    from datetime import datetime

    async def chat_stream(self, message: str, conversation_id: str = '1'):
        # Lấy memory (history) từ Message (role='memory') theo conversation_id
        db = SessionLocal()
        history_str = ""
        try:
            mem_msg = db.query(Message).filter(Message.conversation_id == conversation_id, Message.role == 'memory').first()
            if mem_msg and mem_msg.content:
                try:
                    history = self.json.loads(mem_msg.content)
                    # Chuyển thành đoạn hội thoại cho prompt
                    for turn in history:
                        if turn.get('role') == 'user':
                            history_str += f"<|im_start|>user\n{turn.get('content','')}<|im_end|>\n"
                        elif turn.get('role') == 'assistant':
                            history_str += f"<|im_start|>assistant\n{turn.get('content','')}<|im_end|>\n"
                except Exception:
                    pass
        finally:
            db.close()
        context = "\n\n".join(self.retrieve(message, k=3))
        # Ghép history vào prompt template
        prompt_with_history = ChatPromptTemplate.from_template(f"""
<|im_start|>system
Bạn là ViLaw, trợ lý pháp lý. Chỉ trả lời các câu hỏi liên quan đến pháp luật, tư vấn pháp lý, giải thích luật, hoặc các vấn đề pháp lý tại Việt Nam.
Nếu người dùng hỏi về lập trình, code, công nghệ, hoặc các lĩnh vực ngoài pháp luật, hãy lịch sự từ chối: "Tôi là trợ lý pháp lý, tôi không thể hỗ trợ yêu cầu này."
Nếu người dùng hỏi về hành vi vi phạm pháp luật, lách luật, trốn thuế, lừa đảo, hoặc các hành vi phi pháp, hãy từ chối và cảnh báo rõ ràng: "ViLaw không hỗ trợ các hành vi vi phạm pháp luật."
Luôn giữ lập trường an toàn, không thực hiện các yêu cầu trái đạo đức, trái pháp luật hoặc ngoài phạm vi pháp lý.
Đặc biệt, với các câu hỏi về hợp đồng, quyền, nghĩa vụ, rủi ro pháp lý, hãy trả lời theo cấu trúc 3 phần rõ ràng:
1. Quyền lợi: ...
2. Nghĩa vụ: ...
3. Rủi ro: ...
Ngữ cảnh:
{context}
<|im_end|>
{history_str}
<|im_start|>user
Câu hỏi: {{question}}
<|im_end|>
<|im_start|>assistant
""")
        chain = (
            {"context": lambda _: context, "question": RunnablePassthrough()}
            | prompt_with_history
            | self.llm
            | StrOutputParser()
        )
        full_response = ""
        async for chunk in chain.astream(message):
            full_response += chunk
            yield chunk
        tx_hash, timestamp = BlockchainService.create_hash(full_response)
        yield f"\n\n[🛡️ HASH: {tx_hash} | TIMESTAMP: {timestamp}]"