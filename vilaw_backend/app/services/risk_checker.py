import json
from enum import Enum
from typing import List, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field, validator
from app.services.llm_engine import get_llm
from app.schemas.contract_schema import RiskAnalysisRequest

# --- 1. Định nghĩa Enums & Schema chặt chẽ ---

class RiskSeverity(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class RiskItem(BaseModel):
    severity: RiskSeverity = Field(description="Mức độ nghiêm trọng: High, Medium, hoặc Low")
    clause: str = Field(description="Trích dẫn nguyên văn điều khoản bị lỗi trong hợp đồng")
    issue: str = Field(description="Mô tả ngắn gọn vấn đề pháp lý hoặc rủi ro")
    suggestion: str = Field(description="Đề xuất sửa đổi cụ thể để giảm thiểu rủi ro")
    legal_basis: Optional[str] = Field(None, description="Căn cứ pháp lý (VD: Điều 301 Luật Thương mại 2005). Nếu không chắc chắn thì để null.")

class AIOutputStructure(BaseModel):
    overall_score: int = Field(description="Điểm an toàn pháp lý trên thang 100")
    completeness_status: str = Field(description="Đánh giá tổng quan: Đầy đủ, Thiếu sót nghiêm trọng, v.v.")
    missing_fields: List[str] = Field(description="Danh sách các mục bắt buộc bị thiếu (VD: Chữ ký, Ngày hiệu lực)")
    risks: List[RiskItem] = Field(description="Danh sách chi tiết các rủi ro tìm thấy")

    # Validator để đảm bảo điểm số hợp lệ
    @validator('overall_score')
    def check_score(cls, v):
        if not (0 <= v <= 100):
            return 0
        return v

# --- 2. Service Logic ---

class RiskCheckerService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RiskCheckerService, cls).__new__(cls)
            # Temp = 0.0 để đảm bảo tính nhất quán và nghiêm ngặt nhất
            cls._instance.llm = get_llm(streaming=False, temperature=0.0)
        return cls._instance

    async def analyze_document(self, data: RiskAnalysisRequest) -> dict:
        # Sử dụng Schema có cấu trúc lồng nhau (Nested)
        parser = JsonOutputParser(pydantic_object=AIOutputStructure)

        # Prompt được tinh chỉnh để tránh Hallucination (Bịa luật)
        prompt = ChatPromptTemplate.from_template("""
        <|im_start|>system
        Bạn là Chuyên gia Pháp chế & Kiểm soát Rủi ro Hợp đồng (Legal Risk Compliance) hàng đầu tại Việt Nam.
        Nhiệm vụ: Phân tích văn bản pháp lý cực kỳ nghiêm ngặt để bảo vệ quyền lợi cho khách hàng.
        
        QUY TRÌNH PHÂN TÍCH 4 BƯỚC:
        1. **Kiểm tra hình thức (Completeness):** Rà soát các yếu tố bắt buộc (Chủ thể, Đại diện, Ngày tháng, Chữ ký/Con dấu).
        2. **Đối chiếu pháp luật (Compliance):** So sánh với Bộ luật Dân sự 2015, Luật Thương mại 2005, và các luật chuyên ngành liên quan.
           - Cảnh báo ngay nếu điều khoản trái luật (Vô hiệu).
           - Phát hiện các điều khoản bất lợi, không công bằng.
        3. **Đánh giá rủi ro (Risk Scoring):** Chấm điểm dựa trên mức độ rủi ro tìm thấy.
        4. **Đề xuất (Redlining):** Đưa ra phương án sửa đổi cụ thể.

        QUY TẮC QUAN TRỌNG:
        - **Trích dẫn (clause):** Phải trích dẫn NGUYÊN VĂN từ văn bản input. Không được tự viết lại.
        - **Căn cứ pháp lý:** Chỉ trích dẫn điều luật cụ thể nếu bạn chắc chắn 100%. Nếu không, hãy ghi "Theo quy định pháp luật hiện hành".
        - **JSON Output:** Trả về JSON thuần túy, không markdown.

        {format_instructions}
        <|im_end|>
        
        <|im_start|>user
        LOẠI HỢP ĐỒNG: {contract_type}
        
        NỘI DUNG VĂN BẢN:
        {content}
        <|im_end|>
        
        <|im_start|>assistant
        """)

        chain = prompt | self.llm | parser

        try:
            # Lưu ý: Nếu văn bản quá dài (>10.000 từ), cần có cơ chế cắt nhỏ (Chunking) ở đây
            # Nhưng với các hợp đồng tiêu chuẩn, Gemini Flash/Pro xử lý tốt context window lớn.
            result = await chain.ainvoke({
                "contract_type": data.contract_type,
                "content": data.content,
                "format_instructions": parser.get_format_instructions()
            })
            return result
            
        except Exception as e:
            # Fallback handling chuẩn cấu trúc
            print(f"Lỗi phân tích rủi ro: {e}")
            return AIOutputStructure(
                overall_score=0,
                completeness_status="Lỗi hệ thống khi phân tích",
                missing_fields=[],
                risks=[
                    RiskItem(
                        severity=RiskSeverity.HIGH,
                        clause="N/A",
                        issue=f"Hệ thống không thể đọc văn bản này: {str(e)}",
                        suggestion="Vui lòng kiểm tra lại định dạng văn bản hoặc thử lại sau.",
                        legal_basis=None
                    )
                ]
            ).dict()

# --- Helper test ---
if __name__ == "__main__":
    import asyncio
    async def test():
        service = RiskCheckerService()
        dummy_request = RiskAnalysisRequest(
            contract_type="Hợp đồng lao động",
            content="Điều 1: Lương. Bên A trả cho bên B mức lương 2 triệu đồng/tháng. Thời gian làm việc 12 tiếng/ngày."
        )
        res = await service.analyze_document(dummy_request)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    asyncio.run(test())