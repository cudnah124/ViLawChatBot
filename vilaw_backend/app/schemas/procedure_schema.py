from typing import List, Optional
from pydantic import BaseModel, Field

# --- Phần AI Generate (Thêm description để AI hiểu nhiệm vụ) ---
class DocumentItem(BaseModel):
    name: str = Field(..., description="Tên chính xác của giấy tờ")
    instruction: str = Field(..., description="Yêu cầu cụ thể: bản chính, bản sao y công chứng, hay số lượng bao nhiêu")

class ProcedureStep(BaseModel):
    order: int = Field(..., description="Số thứ tự bước (1, 2, 3...)")
    title: str = Field(..., description="Tên ngắn gọn của bước (VD: Nộp hồ sơ)")
    description: str = Field(..., description="Diễn giải chi tiết các hành động cần làm ở bước này")

class ProcedureGuideResponse(BaseModel):
    title: str = Field(..., description="Tên chuẩn của thủ tục hành chính")
    authority: str = Field(..., description="Cơ quan có thẩm quyền giải quyết (VD: UBND Phường, Sở KHĐT)")
    duration: Optional[str] = Field(None, description="Thời gian giải quyết quy định (VD: 03 ngày làm việc)")
    fee: Optional[str] = Field(None, description="Lệ phí nhà nước (VD: 50.000 VNĐ, hoặc 'Miễn phí')")
    steps: List[ProcedureStep] = Field(..., description="Danh sách các bước thực hiện theo trình tự")
    required_documents: List[DocumentItem] = Field(..., description="Danh sách thành phần hồ sơ bắt buộc")

# --- Phần Dashboard CRUD (Dùng cho API lưu Database) ---
class CreateProcedureRequest(BaseModel):
    title: str
    # Lưu ý: Khi lưu vào DB (PostgreSQL JSONB hoặc MongoDB), cấu trúc này rất tốt
    data: ProcedureGuideResponse 

class UpdateProcedureStatus(BaseModel):
    status: str # "Pending", "Approved", "Rejected"