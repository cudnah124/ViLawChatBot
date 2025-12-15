from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
import os
from app.db.session import SessionLocal
from app.db.models import UserProcedure
from app.services.ocr_service import ocr_image

router = APIRouter()
UPLOAD_DIR = "uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/dashboard/upload_doc")
async def upload_document(
    user_id: int = Form(...),
    procedure_id: int = Form(...),
    document_name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Ensure upload dir exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    # Save file
    file_ext = os.path.splitext(file.filename)[-1]
    # Loại bỏ ký tự không hợp lệ khỏi document_name để tránh lỗi đường dẫn
    safe_doc_name = document_name.replace('/', '_').replace('\\', '_')
    save_path = os.path.join(UPLOAD_DIR, f"user{user_id}_proc{procedure_id}_{safe_doc_name}{file_ext}")
    with open(save_path, "wb") as f:
        f.write(await file.read())
    file_url = f"/{UPLOAD_DIR}/{os.path.basename(save_path)}"

    # OCR recognition
    ocr_result = await ocr_image(save_path)
    detected_type = ocr_result.get("type", "Unknown")

    # Find procedure in DB
    up = db.query(UserProcedure).filter(UserProcedure.id == procedure_id, UserProcedure.user_id == user_id).first()
    if not up:
        raise HTTPException(status_code=404, detail="Procedure not found")
    doc_list = up.data.get("required_documents", [])
    matched = False
    for doc in doc_list:
        if doc["name"] == document_name:
            doc["file_url"] = file_url
            if detected_type.lower() in document_name.lower():
                doc["status"] = "Đã có"
                matched = True
            else:
                doc["status"] = "Sai loại giấy tờ"
    up.data["required_documents"] = doc_list
    db.commit()
    if matched:
        return {"status": "success", "message": "Đã nhận diện đúng loại giấy tờ", "file_url": file_url}
    else:
        return {"status": "warning", "message": f"Tài liệu tải lên dường như là {detected_type}, không khớp với yêu cầu {document_name}.", "file_url": file_url}
