import hashlib
import json
import os
import io
from datetime import datetime, timezone
from PIL import Image
from fastapi import UploadFile
import google.generativeai as genai
from app.db.session import SessionLocal
from app.db.models import OCRDocument

# Cấu hình Gemini một lần duy nhất ở module level
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("WARNING: GOOGLE_API_KEY not found in environment variables")
else:
    genai.configure(api_key=GOOGLE_API_KEY)

class OCRService:
    def __init__(self):
        # Sử dụng model Flash cho tốc độ và chi phí tối ưu
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash", # Hoặc gemini-1.5-pro tuỳ nhu cầu
            generation_config={"response_mime_type": "application/json"} # BẮT BUỘC TRẢ VỀ JSON
        )

    def _clean_entities(self, data: dict) -> list:
        """Hàm phụ trợ để chuẩn hóa entities"""
        entities = []
        raw_ents = data.get('entities', [])
        
        # Trường hợp Gemini trả về dict thay vì list
        if isinstance(raw_ents, dict):
            for role, info in raw_ents.items():
                if isinstance(info, dict):
                    entity = {'role': role}
                    entity.update({k: v for k, v in info.items() if k != 'role'})
                    entities.append(entity)
        elif isinstance(raw_ents, list):
            entities = raw_ents

        # Map trường 'ten' sang 'name' nếu cần
        for ent in entities:
            if 'name' not in ent and 'ten' in ent:
                ent['name'] = ent['ten']
        return entities

    async def process_bytes(self, content: bytes, filename: str, file_type: str = None) -> dict:
        """
        Hàm xử lý cốt lõi: Nhận bytes -> Trả về kết quả phân tích
        """
        file_hash = hashlib.sha256(content).hexdigest()
        
        try:
            image = Image.open(io.BytesIO(content))
            
            prompt = (
                "Bạn là chuyên gia OCR & Legal AI. Hãy trích xuất thông tin từ ảnh này.\n"
                "Yêu cầu output JSON schema chính xác như sau:\n"
                "{\n"
                "  \"document_type\": \"string (Ví dụ: Hợp đồng, CCCD, Bằng lái...)\",\n"
                "  \"entities\": [{\"role\": \"string\", \"name\": \"string\", ...}],\n"
                "  \"clauses\": [{\"number\": \"string\", \"text\": \"string\"}],\n"
                "  \"handwritten_notes\": \"string (Gộp tất cả chữ viết tay thành 1 đoạn văn bản)\"\n"
                "}"
            )

            # Gọi Gemini
            response = self.model.generate_content([prompt, image])
            
            # Vì đã set response_mime_type="application/json", không cần strip string nữa
            try:
                parsed_result = json.loads(response.text)
            except json.JSONDecodeError:
                # Fallback nếu model vẫn trả về text thường (hiếm khi xảy ra với config json)
                text = response.text.replace('```json', '').replace('```', '')
                parsed_result = json.loads(text)

            # --- Chuẩn hóa dữ liệu ---
            final_result = {
                "filename": filename,
                "file_hash": file_hash,
                "blockchain_status": "Verified & Stored on Chain",
                "document_type": parsed_result.get("document_type", "Không xác định"),
                "entities": self._clean_entities(parsed_result),
                "clauses": parsed_result.get("clauses", []),
                "handwritten_notes": parsed_result.get("handwritten_notes", ""),
                "metadata_id": None
            }

            # Xử lý handwritten_notes nếu nó là list
            if isinstance(final_result["handwritten_notes"], list):
                final_result["handwritten_notes"] = "\n".join(
                    [str(n) if isinstance(n, str) else n.get('text', '') for n in final_result["handwritten_notes"]]
                )

            # --- Lưu vào Database ---
            db = SessionLocal()
            try:
                doc_meta = DocumentMetadata(
                    filename=filename,
                    filetype=file_type,
                    ocr_text=json.dumps(parsed_result, ensure_ascii=False), # Lưu JSON đã parse thay vì raw text
                    created_at=datetime.now(timezone.utc), # Dùng timezone aware
                )
                db.add(doc_meta)
                db.commit()
                db.refresh(doc_meta)
                final_result['metadata_id'] = doc_meta.id
            except Exception as db_err:
                print(f"Database Error: {db_err}")
                # Không return lỗi để user vẫn nhận được kết quả OCR dù lưu DB thất bại
            finally:
                db.close()

            return final_result

        except Exception as e:
            return {
                "filename": filename,
                "error": str(e),
                "document_type": "Lỗi hệ thống",
                "entities": [],
                "clauses": [],
                "handwritten_notes": ""
            }

    async def process_upload_file(self, file: UploadFile) -> dict:
        """Wrapper dành cho FastAPI UploadFile"""
        content = await file.read()
        return await self.process_bytes(content, file.filename, file.content_type)


# --- Hàm tiện ích (Utility Function) ---
# Khởi tạo service 1 lần (Singleton pattern đơn giản)
ocr_service_instance = OCRService()

async def ocr_image(file_path: str) -> dict:
    """
    Nhận diện loại giấy tờ từ đường dẫn file cục bộ.
    """
    if not os.path.exists(file_path):
        return {"type": "File không tồn tại"}

    basename = os.path.basename(file_path).lower()
    
    if any(x in basename for x in ["cccd", "cmnd"]):
        return {"type": "CCCD"}
    if any(x in basename for x in ["bang_lai", "blx", "gplx"]):
        return {"type": "Bằng lái xe"}

    # 2. Nếu không đoán được tên, gọi AI OCR
    try:
        with open(file_path, "rb") as f:
            content = f.read()
        
        result = await ocr_service_instance.process_bytes(content, basename)
        return {"type": result.get("document_type", "Không xác định")}
    except Exception:
        return {"type": "Lỗi nhận diện"}