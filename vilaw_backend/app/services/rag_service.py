import os
import hashlib
from datetime import datetime
from typing import List

# 1. Import thư viện của bạn
import torch
from transformers import AutoTokenizer, AutoModel, RobertaModel
from langchain_core.embeddings import Embeddings # Class cha để custom
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from app.core.config import settings
from app.services.llm_engine import get_llm
from app.services.blockchain import BlockchainService

# ---------------------------------------------------------
# 2. ĐỊNH NGHĨA CLASS CUSTOM EMBEDDING (Dùng code của bạn)
# ---------------------------------------------------------
class VietnameseSBERTEmbeddings(Embeddings):
    def _mean_pooling(self, model_output, attention_mask):
        """
        Mean Pooling - lấy embedding trung bình cho mỗi câu
        """
        token_embeddings = model_output[0]  # First element of output contains token embeddings
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

    def __init__(self, model_name: str = "keepitreal/vietnamese-sbert"):
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            # Thay AutoModel bằng RobertaModel
            self.model = RobertaModel.from_pretrained(model_name)
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model.to(self.device)
            self.model.eval()
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {e}")

    def _compute_embedding(self, texts: List[str]) -> List[List[float]]:
        try:
            # Tokenize với max_length để tránh quá dài
            encoded_input = self.tokenizer(
                texts, 
                padding=True, 
                truncation=True, 
                max_length=512,  # Thêm giới hạn
                return_tensors='pt'
            )
            encoded_input = {k: v.to(self.device) for k, v in encoded_input.items()}

            with torch.no_grad():
                model_output = self.model(**encoded_input)

            sentence_embeddings = self._mean_pooling(
                model_output, 
                encoded_input['attention_mask']
            )
            
            return sentence_embeddings.cpu().tolist()
        except Exception as e:
            raise RuntimeError(f"Embedding computation failed: {e}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Dùng cho list văn bản (Khi nạp data)"""
        return self._compute_embedding(texts)

    def embed_query(self, text: str) -> List[float]:
        """Dùng cho 1 câu hỏi (Khi chat)"""
        return self._compute_embedding([text])[0]

# ---------------------------------------------------------
# 3. SỬ DỤNG CLASS MỚI TRONG RAG SERVICE
# ---------------------------------------------------------
class RAGService:
    def __init__(self):
        # Thay vì dùng HuggingFaceEmbeddings có sẵn, ta dùng Class tự viết
        self.embedding_model = VietnameseSBERTEmbeddings()

        # Kết nối Pinecone
        self.vector_db = PineconeVectorStore.from_existing_index(
            index_name=settings.PINECONE_INDEX_NAME,
            embedding=self.embedding_model
        )
        
        self.retriever = self.vector_db.as_retriever(search_kwargs={"k": 3})
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

    def format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)

    async def chat_stream(self, question: str):
        chain = (
            {"context": self.retriever | self.format_docs, "question": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )

        full_response = ""
        async for chunk in chain.astream(question):
            full_response += chunk
            yield chunk

        tx_hash, timestamp = BlockchainService.create_hash(full_response)
        yield f"\n\n[🛡️ HASH: {tx_hash} | TIMESTAMP: {timestamp}]"