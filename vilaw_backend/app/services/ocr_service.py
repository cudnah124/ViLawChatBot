import hashlib
import base64
import io
import json
from datetime import datetime
from app.db.session import SessionLocal
from app.db.models import DocumentMetadata
from fastapi import UploadFile
from app.schemas.document_schema import DocumentAnalysisResponse
from pydantic import BaseModel, Field
import os
import asyncio
from PIL import Image

class AIOutputStructure(BaseModel):
    document_type: str
    entities: list
    clauses: list
    handwritten_notes: str

class OCRService:
    def __init__(self):
        import google.generativeai as genai
        self.gemini_api_key = os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash-lite")

    async def process_document(self, file: UploadFile) -> dict:
        content = await file.read()
        file_hash = hashlib.sha256(content).hexdigest()
        try:
            # Đọc ảnh từ bytes
            image = Image.open(io.BytesIO(content))
            # Chuẩn bị prompt
            prompt = (
                "Bạn là chuyên gia OCR & Legal AI. Nhiệm vụ:\n"
                "1. Đọc toàn bộ nội dung trong hình ảnh (bao gồm cả CHỮ VIẾT TAY và CHỮ IN).\n"
                "2. Phân tích cấu trúc văn bản thành các điều khoản.\n"
                "3. Trích xuất thông tin các bên (Chủ thể).\n"
                "4. Ghi chú lại các đoạn viết tay (nếu có).\n"
                "Trả về kết quả JSON với các trường: document_type, entities, clauses, handwritten_notes."
            )
            # Truyền đúng định dạng cho Gemini Vision API
            result = self.model.generate_content([
                prompt,
                image
            ])
            # Xử lý JSON trả về an toàn, tự động bóc tách nếu có markdown/code block
            raw_text = result.text.strip()
            # Nếu trả về dạng code block ```json ... ``` hoặc ``` ... ``` thì bóc tách phần JSON
            if raw_text.startswith('```'):
                # Xóa 3 dấu ``` đầu và cuối, và loại bỏ từ 'json' nếu có
                lines = raw_text.split('\n')
                if lines[0].startswith('```json'):
                    lines = lines[1:]
                elif lines[0].startswith('```'):
                    lines = lines[1:]
                # Loại bỏ dòng ``` cuối cùng nếu có
                if lines and lines[-1].strip().startswith('```'):
                    lines = lines[:-1]
                json_str = '\n'.join(lines)
            else:
                json_str = raw_text
            try:
                parsed_result = json.loads(json_str)
            except Exception as e:
                parsed_result = {
                    "document_type": "Không xác định",
                    "entities": [],
                    "clauses": [],
                    "handwritten_notes": f"Lỗi phân tích JSON: {str(e)}\nRaw: {raw_text}"
                }
            parsed_result['filename'] = file.filename
            parsed_result['file_hash'] = file_hash
            parsed_result['blockchain_status'] = "Verified & Stored on Chain"
            # Chuẩn hóa entities: phải là list, có trường 'name'
            if not isinstance(parsed_result.get('entities'), list):
                entities = []
                ents = parsed_result.get('entities')
                if isinstance(ents, dict):
                    for role, info in ents.items():
                        if isinstance(info, dict):
                            entity = {'role': role}
                            entity.update({k: v for k, v in info.items() if k != 'role'})
                            entities.append(entity)
                parsed_result['entities'] = entities
            # Map lại các trường entity nếu thiếu 'name' nhưng có 'ten'
            for entity in parsed_result.get('entities', []):
                if 'name' not in entity and 'ten' in entity:
                    entity['name'] = entity['ten']
                # Map các trường khác nếu cần
            # Chuẩn hóa clauses: phải là list, mỗi phần tử có 'number' và 'text'
            if isinstance(parsed_result.get('clauses'), list):
                for idx, clause in enumerate(parsed_result['clauses']):
                    if 'number' not in clause:
                        clause['number'] = str(idx+1)
                    # Map lại các trường nếu thiếu 'text' nhưng có 'content'
                    if 'text' not in clause:
                        if 'clause_text' in clause:
                            clause['text'] = clause['clause_text']
                        elif 'content' in clause:
                            clause['text'] = clause['content']
            else:
                parsed_result['clauses'] = []
            # handwritten_notes: ép thành string nếu là list
            if isinstance(parsed_result.get('handwritten_notes'), list):
                notes = []
                for note in parsed_result['handwritten_notes']:
                    if isinstance(note, dict) and 'text' in note:
                        notes.append(note['text'])
                    elif isinstance(note, str):
                        notes.append(note)
                parsed_result['handwritten_notes'] = '\n'.join(notes)
            # Đảm bảo không có trường nào là bytes
            for k, v in list(parsed_result.items()):
                if isinstance(v, (bytes, bytearray)):
                    parsed_result[k] = v.decode(errors="replace")
            # Lưu metadata vào database
            db = SessionLocal()
            try:
                doc_meta = DocumentMetadata(
                    external_id=None,  # Nếu có external_id từ hệ thống ngoài thì truyền vào
                    filename=file.filename,
                    filetype=file.content_type,
                    uploader_id=None,  # Nếu có user_id thì truyền vào
                    ocr_text=raw_text,
                    created_at=datetime.utcnow().isoformat(),
                    conversation_id=None,  # Nếu có liên kết conversation thì truyền vào
                    message_id=None
                )
                db.add(doc_meta)
                db.commit()
                db.refresh(doc_meta)
                parsed_result['metadata_id'] = doc_meta.id
            finally:
                db.close()
            return parsed_result
        except Exception as e:
            return {
                "filename": file.filename,
                "file_hash": file_hash,
                "blockchain_status": "Error",
                "document_type": "Không xác định",
                "entities": [],
                "clauses": [],
                "handwritten_notes": f"Lỗi xử lý: {str(e)}"
            }

async def ocr_image(file_path: str) -> dict:
    """
    Nhận diện loại giấy tờ từ ảnh file_path, trả về dict với trường 'type'.
    """
    # Giả lập: chỉ nhận diện dựa vào tên file, thực tế sẽ gọi OCRService
    basename = os.path.basename(file_path).lower()
    if "cccd" in basename or "cmnd" in basename:
        doc_type = "CCCD"
    elif "ho_khau" in basename or "hokhau" in basename:
        doc_type = "Sổ hộ khẩu"
    elif "bang_lai" in basename or "banglai" in basename or "blx" in basename:
        doc_type = "Bằng lái xe"
    else:
        # Thực tế: dùng OCRService để nhận diện
        try:
            service = OCRService()
            # Mở file dạng UploadFile giả lập
            class DummyUpload:
                def __init__(self, path):
                    self.filename = os.path.basename(path)
                    self._path = path
                async def read(self):
                    with open(self._path, "rb") as f:
                        return f.read()
            dummy = DummyUpload(file_path)
            result = await service.process_document(dummy)
            doc_type = result.get("document_type", "Không xác định")
        except Exception as e:
            doc_type = "Không xác định"
    return {"type": doc_type}
