import uvicorn
from fastapi import FastAPI
from app.api.v1 import chat

app = FastAPI(title="ViLaw Backend API", version="1.0")

# Đăng ký các router
app.include_router(chat.router, prefix="/api/v1/chat", tags=["AI Chat"])

@app.get("/")
def health_check():
    return {"status": "ok", "message": "ViLaw Server is running"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)