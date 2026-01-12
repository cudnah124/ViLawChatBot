from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ContractDraftRequest(BaseModel):
	document_type: str = Field(..., description="Loại văn bản. Một trong: 'Đơn Khiếu Nại','Hợp Đồng Thuê Nhà','Đơn xin Việc','Đơn tố cáo'")
	summary: str = Field(..., description="Tóm tắt ngắn do người dùng cung cấp — là nguồn chính để soạn thảo văn bản.")
	metadata: Dict[str, str] = Field(default_factory=dict, description="Thông tin bổ sung cho template (ví dụ: name, address, date, content, v.v.)")


class ContractDraftResponse(BaseModel):
    content_preview: str    # Nội dung text để hiển thị nhanh
    risk_report: str        # Kết quả quét rủi ro
    download_url: str       # Đường dẫn tải file .docx
    needs_more_info: bool = False
    questions: Optional[List[str]] = None





class RiskPoint(BaseModel):
	severity: str           # "High", "Medium", "Low"
	clause: Optional[str] = None   # Đoạn văn bản bị lỗi (nếu tìm thấy)
	issue: str = ""
	suggestion: str = ""
	legal_basis: str = ""


class RiskAnalysisRequest(BaseModel):
	content: str
	contract_type: str


class RiskAnalysisResponse(BaseModel):
	overall_score: int
	completeness_status: str
	missing_fields: List[str]
	risks: List[RiskPoint]
