
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from app.services.llm_engine import get_llm
from app.schemas.contract_schema import RiskAnalysisRequest, RiskAnalysisResponse, RiskPoint

# Định nghĩa cấu trúc JSON mong muốn cho AI hiểu
class AIOutputStructure(BaseModel):
    overall_score: int = Field(description="Điểm an toàn từ 0-100")
    completeness_status: str = Field(description="Đánh giá tổng quan tính đầy đủ")
    missing_fields: list[str] = Field(description="Danh sách các mục bắt buộc bị thiếu")
    risks: list[dict] = Field(description="Danh sách rủi ro gồm: severity, clause, issue, suggestion, legal_basis")

class RiskCheckerService:
    def __init__(self):
        # Dùng model thông minh nhất có thể (GPT-4o hoặc tương đương) để review chính xác
        self.llm = get_llm(streaming=False, temperature=0.1) # Temp thấp để check nghiêm ngặt

    async def analyze_document(self, data: RiskAnalysisRequest) -> dict:
        """
        Phân tích rủi ro toàn diện
        """
        parser = JsonOutputParser(pydantic_object=AIOutputStructure)

        prompt = ChatPromptTemplate.from_template("""
        <|im_start|>system
        Bạn là Chuyên gia Kiểm soát Rủi ro Hợp đồng (Legal Risk Auditor) tại Việt Nam.
        Nhiệm vụ: Rà soát văn bản và phát hiện lỗi pháp lý.
        
        HÃY THỰC HIỆN 4 BƯỚC KIỂM TRA SAU:
        1. **Completeness Check:** Kiểm tra xem có thiếu: Chủ thể, Ngày tháng, Chữ ký, Con dấu, Hiệu lực không?
        2. **Conflict & Compliance:** - So sánh với Luật pháp Việt Nam hiện hành (đặc biệt là Bộ luật Dân sự, Thương mại, Lao động tùy ngữ cảnh).
           - Phát hiện điều khoản trái luật (Vô hiệu).
           - Phát hiện mâu thuẫn nội tại (VD: Điều trên đá điều dưới).
        3. **Risk Scoring:** Chấm điểm an toàn (0-100).
        4. **Redlining:** Đề xuất sửa đổi cụ thể cho từng lỗi.

        ĐỊNH DẠNG OUTPUT:
        Chỉ trả về JSON thuần túy theo cấu trúc sau (Không markdown):
        {format_instructions}
        <|im_end|>
        
        <|im_start|>user
        Loại văn bản: {contract_type}
        Nội dung cần rà soát:
        {content}
        <|im_end|>
        
        <|im_start|>assistant
        """)

        chain = prompt | self.llm | parser

        try:
            # Gọi AI phân tích
            result = await chain.ainvoke({
                "contract_type": data.contract_type,
                "content": data.content,
                "format_instructions": parser.get_format_instructions()
            })
            return result
        except Exception as e:
            # Fallback nếu AI trả về JSON lỗi
            return {
                "overall_score": 0,
                "completeness_status": "Lỗi phân tích",
                "missing_fields": [],
                "risks": [{
                    "severity": "High",
                    "issue": f"Không thể phân tích văn bản: {str(e)}",
                    "suggestion": "Vui lòng thử lại",
                    "legal_basis": "N/A",
                    "clause": ""
                }]
            }
