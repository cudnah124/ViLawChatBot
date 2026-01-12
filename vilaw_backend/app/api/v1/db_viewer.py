import os
import shutil
import json
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import LawChunk, OCRDocument, LawDocument
from app.services.rag_service import RAGService

router = APIRouter()
UPLOAD_DIR = "static/docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@router.get("/db/ocr-documents", tags=["Admin Dashboard"])
def list_ocr_documents(db: Session = Depends(get_db)):
    docs = db.query(OCRDocument).order_by(OCRDocument.created_at.desc()).all()
    result = []
    for doc in docs:
        ext = None
        if doc.filename and "." in doc.filename:
            ext = doc.filename.rsplit('.', 1)[-1].lower()
        result.append({
            "id": doc.id,
            "filename": doc.filename,
            "filetype": ext,
            "created_at": doc.created_at,
            "ocr_text_preview": doc.ocr_text[:100] + "..." if doc.ocr_text else "Chưa có nội dung"
        })
    return result

@router.get("/db/laws", tags=["Admin Dashboard"])
def list_laws(db: Session = Depends(get_db)):
    laws = db.query(LawChunk).order_by(LawChunk.id.desc()).all()
    return [
        {
            "id": law.id,
            "title": law.title,
            "content_preview": law.content[:100] + "..." if law.content else "",
            "document_id": law.document_id
        }
        for law in laws
    ]


@router.post("/db/upload", tags=["Admin Dashboard"])
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload file để dạy cho AI.
    - .json: Import vào bảng LawDocument & LawChunk (Dùng cho RAG).
    - .pdf: Import vào bảng OCRDocument (Lưu trữ file thô/OCR).
    """
    # 1. Lưu file vật lý
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb+") as buffer:
        shutil.copyfileobj(file.file, buffer)

    imported_count = 0
    skipped_count = 0
    action_msg = ""
    trigger_rag = False

    # JSON file processing
    if file.filename.lower().endswith(".json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            items = data if isinstance(data, list) else [data]
            

            doc_name = file.filename.rsplit('.', 1)[0].replace("_", " ")
            
            law_doc = db.query(LawDocument).filter(LawDocument.name == doc_name).first()
            if not law_doc:
                law_doc = LawDocument(name=doc_name, code_number="N/A")
                db.add(law_doc)
                db.commit()
                db.refresh(law_doc) # Lấy ID thật sự từ DB


            existing_chunks = db.query(LawChunk.title).filter(LawChunk.document_id == law_doc.id).all()
            existing_titles = {chunk.title for chunk in existing_chunks}


            new_chunks = []
            for item in items:
                title = item.get("title", "Không tiêu đề")
                content = item.get("content", "")
                
                if title in existing_titles:
                    skipped_count += 1
                    continue

                if content.strip():
                    new_chunk = LawChunk(
                        title=title,
                        content=content,
                        document_id=law_doc.id
                    )
                    new_chunks.append(new_chunk)
                    imported_count += 1
            
            if new_chunks:
                db.add_all(new_chunks)
                db.commit()
                trigger_rag = True # Có dữ liệu mới thì mới cần học lại

            action_msg = f"Đã import {imported_count} điều luật vào '{doc_name}'. Bỏ qua {skipped_count} trùng lặp."

        except json.JSONDecodeError:
            return {"status": "error", "message": "File JSON sai cú pháp."}
        except Exception as e:
            db.rollback()
            return {"status": "error", "message": f"Lỗi xử lý JSON: {str(e)}"}


    # PDF file processing
    elif file.filename.lower().endswith(".pdf"):
        text_content = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    extract = page.extract_text()
                    if extract: text_content += extract + "\n"
        except Exception as e:
            print(f"Lỗi đọc PDF: {e}")
            
        if not text_content.strip():
            return {"status": "warning", "message": "File PDF không có text (ảnh scan)."}
            
        # Lưu vào bảng OCRDocument riêng biệt
        new_doc = OCRDocument(
            filename=file.filename,
            ocr_text=text_content,
            # filetype="pdf" # (Bỏ comment nếu model OCRDocument có cột này)
        )
        db.add(new_doc)
        db.commit()
        action_msg = "Đã lưu file PDF và nội dung OCR."


    else:
        return {"status": "error", "message": "Chỉ hỗ trợ .json hoặc .pdf"}

    # Trigger RAG refresh
    if trigger_rag:
        background_tasks.add_task(RAGService.refresh_knowledge)
        action_msg += " AI đang cập nhật dữ liệu..."

    return {
        "status": "success",
        "message": action_msg,
        "imported_count": imported_count,
        "skipped_count": skipped_count
    }


@router.delete("/db/law-documents/{doc_id}", tags=["Admin Dashboard"])
def delete_law_document(
    doc_id: int, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Xóa một bộ luật (LawDocument).
    Tự động xóa tất cả các điều khoản con (LawChunk) nhờ Cascade Delete.
    """

    doc = db.query(LawDocument).filter(LawDocument.id == doc_id).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Không tìm thấy văn bản luật này")


    db.delete(doc)
    db.commit()

    # Refresh RAG index
    background_tasks.add_task(RAGService.refresh_knowledge)

    return {"status": "success", "message": f"Đã xóa bộ luật '{doc.name}' và cập nhật lại AI."}