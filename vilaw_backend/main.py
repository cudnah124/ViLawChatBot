import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Import các router
from app.api.v1 import chat, contracts, documents, procedures, upload

# --- 1. Lifespan: Quản lý khởi động & tắt server ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Tạm thời comment đoạn này lại:
    # await init_db() 
    yield
    # Shutdown
    pass

app = FastAPI(title="ViLaw Backend API", version="1.0", lifespan=lifespan)

# --- 2. CORS: Cần thiết lập kỹ trên Production ---
# Trên Render, bạn nên thay ["*"] bằng domain frontend của bạn (ví dụ: https://vilaw-frontend.onrender.com)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 3. Đăng ký Router ---
app.include_router(chat.router, prefix="/api/v1/chat", tags=["AI Chat"])
app.include_router(contracts.router, prefix="/api/v1/contracts", tags=["Contracts"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Document Analysis"])
app.include_router(procedures.router, prefix="/api/v1/procedures", tags=["Procedures"])
app.include_router(upload.router, prefix="/api/v1", tags=["Upload"])

# --- 4. Xử lý Static Files (Lưu ý vấn đề mất dữ liệu trên Render) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(os.path.join(STATIC_DIR, "docs"), exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def health_check():
    return {"status": "ok", "message": "ViLaw Server is running on Render"}

# --- 5. Entry Point cho Render ---
if __name__ == "__main__":
    # Render sẽ cung cấp PORT qua biến môi trường. Nếu không có (chạy local), dùng 8000
    port = int(os.environ.get("PORT", 8000))
    
    # Kiểm tra xem đang chạy ở đâu để bật/tắt reload
    # Bạn nên set biến môi trường ENV=production trên dashboard Render
    environment = os.environ.get("ENV", "development")
    is_reload = environment == "development"

    print(f"Starting server on port {port} in {environment} mode...")
    
    uvicorn.run(
        "main:app", 
        host="0.0.0.0",  # Bắt buộc là 0.0.0.0 trên Render
        port=port, 
        reload=is_reload
    )
