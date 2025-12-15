# ViLawChatBot API – Hướng dẫn tích hợp cho Frontend

## 1. Chatbot tư vấn pháp luật
- **Endpoint:** `POST /api/v1/chat/stream`
- **Request:**
  ```json
  {
    "question": "<nội dung câu hỏi>"
  }
  ```
- **Response:**
  - Trả về text (stream hoặc plain text)
- **Frontend sử dụng:**
  - Gửi request với trường `question`.
  - Hiển thị text trả về trực tiếp cho user.

---

## 2. Soạn thảo hợp đồng/thư mẫu
- **Endpoint:** `POST /api/v1/contracts/draft`
- **Request:**
  ```json
  {
    "contract_type": "Hợp đồng lao động",
    "party_a": "Nguyễn Văn A",
    "party_b": "Công ty B",
    "key_terms": {
      "Lương": "10 triệu",
      "Thời hạn": "12 tháng"
    }
  }
  ```
- **Response:**
  ```json
  {
    "content_preview": "...nội dung hợp đồng...",
    "risk_report": "...tóm tắt rủi ro...",
    "download_url": "http://.../file.docx"
  }
  ```
- **Frontend sử dụng:**
  - Gửi đúng các trường như trên.
  - Hiển thị bản nháp, cảnh báo rủi ro, cho phép tải file.

---

## 3. Kiểm tra rủi ro hợp đồng
- **Endpoint:** `POST /api/v1/contracts/check-risk`
- **Request:**
  ```json
  {
    "content": "Nội dung hợp đồng cần kiểm tra",
    "contract_type": "Hợp đồng lao động"
  }
  ```
- **Response:**
  ```json
  {
    "overall_score": 85,
    "completeness_status": "Đầy đủ",
    "missing_fields": [],
    "risks": [
      {
        "severity": "High",
        "clause": "...",
        "issue": "Thiếu ngày ký",
        "suggestion": "Bổ sung ngày ký",
        "legal_basis": "Điều 123 BLDS"
      }
    ]
  }
  ```
- **Frontend sử dụng:**
  - Gửi nội dung hợp đồng và loại hợp đồng.
  - Hiển thị điểm số, trạng thái, danh sách rủi ro, gợi ý.

---

## 4. Phân tích tài liệu upload (OCR)
- **Endpoint:** `POST /api/v1/documents/analyze`
- **Request:**
  - Gửi file ảnh (JPG/PNG) qua form-data, key là `file`.
- **Response:**
  ```json
  {
    "filename": "file.jpg",
    "file_hash": "...",
    "document_type": "CCCD",
    "entities": [...],
    "clauses": [...],
    "handwritten_notes": "...",
    "metadata_id": 1
  }
  ```
- **Frontend sử dụng:**
  - Upload file, nhận text và metadata, hiển thị cho user.

---

## 5. Thủ tục hành chính & Dashboard
- **Lấy hướng dẫn quy trình:**
  - **Endpoint:** `GET /api/v1/procedures/guide?query=<tên thủ tục>`
  - **Response:**
    ```json
    {
      "steps": ["Bước 1...", "Bước 2..."]
    }
    ```
- **Lấy dashboard trạng thái hồ sơ:**
  - **Endpoint:** `GET /api/v1/procedures/dashboard?user_id=<id>`
  - **Response:**
    ```json
    [
      {"id": 1, "title": "Ly hôn", "status": "In Progress", "completion": "30%"}
    ]
    ```
- **Frontend sử dụng:**
  - Gọi API, hiển thị hướng dẫn từng bước, trạng thái hồ sơ cho user.

---

**Lưu ý cho frontend:**
- Luôn gửi đúng tên trường như ví dụ.
- Xử lý lỗi HTTP (400/404/422) để báo cho user.
- Có thể dùng fetch/axios hoặc bất kỳ thư viện HTTP nào.
- Nếu API trả về text (không phải JSON), chỉ cần hiển thị text đó.
