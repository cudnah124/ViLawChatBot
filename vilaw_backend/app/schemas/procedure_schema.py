from pydantic import BaseModel
from typing import List, Optional

# --- Phần AI Generate ---
class DocumentItem(BaseModel):
    name: str
    instruction: str # Hướng dẫn chuẩn bị (VD: Photo công chứng)

class ProcedureStep(BaseModel):
    order: int
    title: str
    description: str

class ProcedureGuideResponse(BaseModel):
    title: str
    authority: str          # Cơ quan thẩm quyền
    duration: str           # Thời gian giải quyết
    fee: str                # Lệ phí
    steps: List[ProcedureStep]
    required_documents: List[DocumentItem]

# --- Phần Dashboard CRUD ---
class CreateProcedureRequest(BaseModel):
    title: str
    data: ProcedureGuideResponse # Bê nguyên kết quả AI trả về để lưu

class UpdateProcedureStatus(BaseModel):
    status: str # "Pending", "Done"...
