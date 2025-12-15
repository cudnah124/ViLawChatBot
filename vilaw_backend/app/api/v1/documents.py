from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.ocr_service import OCRService
from app.schemas.document_schema import DocumentAnalysisResponse, DocumentMetadataResponse
from app.db.session import SessionLocal
from app.db.models import DocumentMetadata

router = APIRouter()
ocr_service = OCRService()

@router.get("/metadata/{metadata_id}", response_model=DocumentMetadataResponse)
async def get_document_metadata(metadata_id: int):
    db = SessionLocal()
    try:
        doc = db.query(DocumentMetadata).filter(DocumentMetadata.id == metadata_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Metadata not found")
        return doc
    finally:
        db.close()

@router.post("/analyze", response_model=DocumentAnalysisResponse)
async def analyze_document_endpoint(file: UploadFile = File(...)):
    """
    API 4.0: Phân tích tài liệu Upload.
    - Hỗ trợ: Ảnh (JPG, PNG). (PDF cần convert sang ảnh ở Client hoặc Backend).
    - Output: JSON cấu trúc + Mã Hash bảo mật.
    """
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Hiện tại bản Demo chỉ hỗ trợ file ảnh (JPG/PNG).")
    result = await ocr_service.process_document(file)
    # Đảm bảo không trả về raw bytes, chỉ trả về JSON hợp lệ
    if isinstance(result, dict):
        for k, v in list(result.items()):
            if isinstance(v, (bytes, bytearray)):
                del result[k]
    return result
