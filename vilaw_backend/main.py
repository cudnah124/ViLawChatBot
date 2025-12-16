import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Import các router
from app.api.v1 import chat, contracts, documents, procedures, upload, db_viewer

# --- 1. Lifespan: Quản lý khởi động & tắt server ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Logic khi server khởi động
    print("--- Server Starting ---")
    try:
        from app.db.init import init_db
        # Lưu ý: Đảm bảo biến môi trường DATABASE_URL đã được set trên Render
        init_db()
        print("Database connection initialized.")
    except Exception as e:
        print(f"WARNING: Database initialization failed: {e}")

    yield
    # Shutdown
    pass

app = FastAPI(title="ViLaw Backend API", version="1.0", lifespan=lifespan)

# --- 2. CORS: Cần thiết lập kỹ trên Production ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=".*",
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
app.include_router(db_viewer.router, prefix="/api/v1", tags=["DB Viewer"])

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
