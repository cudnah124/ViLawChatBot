from typing import Dict
from pydantic import BaseModel, Field

class ContractDraftRequest(BaseModel):
	contract_type: str = Field(..., description="Loại văn bản (Hợp đồng lao động, Hợp đồng dịch vụ...)")
	party_a: str = Field(..., description="Bên A")
	party_b: str = Field(..., description="Bên B")
	key_terms: Dict[str, str] = Field(..., description="Các điều khoản chính (Lương, Thời hạn, Địa điểm...)")

class ContractDraftResponse(BaseModel):
	content_preview: str    # Nội dung text để hiển thị nhanh
	risk_report: str        # Kết quả quét rủi ro
	download_url: str       # Đường dẫn tải file .docx

# --- Risk Checker Schemas ---
from typing import List, Optional

class RiskPoint(BaseModel):
	severity: str           # "High", "Medium", "Low"
	clause: Optional[str]   # Đoạn văn bản bị lỗi (nếu tìm thấy)
	issue: str              # Mô tả vấn đề (VD: Thiếu điều khoản, Trái luật...)
	suggestion: str         # Gợi ý sửa đổi (Redlining)
	legal_basis: str        # Căn cứ pháp lý (Điều luật vi phạm)

class RiskAnalysisRequest(BaseModel):
	content: str            # Nội dung hợp đồng cần check
	contract_type: str      # VD: "Hợp đồng lao động" (để AI biết đường so sánh)

class RiskAnalysisResponse(BaseModel):
	overall_score: int      # 0 - 100 (Càng cao càng an toàn)
	completeness_status: str # "Đầy đủ" hoặc "Thiếu thông tin quan trọng"
	missing_fields: List[str] # Danh sách các mục còn thiếu (Ngày, Chữ ký...)
	risks: List[RiskPoint]    # Chi tiết các rủi ro tìm thấy
