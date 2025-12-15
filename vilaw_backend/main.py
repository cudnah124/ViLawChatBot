import os
from fastapi.staticfiles import StaticFiles
from app.api.v1 import contracts

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import chat, documents, procedures, upload



app = FastAPI(title="ViLaw Backend API", version="1.0")

# Thêm CORS middleware để cho phép frontend truy cập
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Đăng ký các router
app.include_router(chat.router, prefix="/api/v1/chat", tags=["AI Chat"])
app.include_router(contracts.router, prefix="/api/v1/contracts", tags=["Contracts"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Document Analysis"])
app.include_router(procedures.router, prefix="/api/v1/procedures", tags=["Procedures"])
app.include_router(upload.router, prefix="/api/v1", tags=["Upload"])

# Mount thư mục static để user tải file về
os.makedirs("static/docs", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def health_check():
    return {"status": "ok", "message": "ViLaw Server is running"}

if __name__ == "__main__":
    # Tạo tất cả các bảng nếu chưa có
    from app.db.session import engine
    from app.db import models
    models.Base.metadata.create_all(bind=engine)
    port = int(os.environ.get("PORT", 8000))
    print("App started, will run uvicorn on port", port, flush=True)
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)