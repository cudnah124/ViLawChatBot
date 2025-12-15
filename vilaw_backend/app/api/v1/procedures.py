
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.services.procedure_engine import ProcedureEngine
from app.schemas.procedure_schema import ProcedureGuideResponse, CreateProcedureRequest
from app.db.session import SessionLocal
from app.db.models import UserProcedure


router = APIRouter()
engine = ProcedureEngine()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 1. API Hỏi thủ tục (AI Generate)
@router.get("/guide", response_model=ProcedureGuideResponse)
async def get_procedure_guide(query: str):
    return await engine.generate_guide(query)

# 2. API Lưu vào Dashboard (Start Tracking)
@router.post("/track")
async def track_procedure(request: CreateProcedureRequest, db: Session = Depends(get_db)):
    user_procedure = UserProcedure(
        user_id=1,  # For demo, always 1. In real app, get from auth
        title=request.title,
        status="In Progress",
        data=request.data.dict()
    )
    db.add(user_procedure)
    db.commit()
    db.refresh(user_procedure)
    return {"status": "success", "message": "Đã thêm vào Dashboard theo dõi"}

# 3. API Lấy danh sách đang theo dõi
@router.get("/dashboard")
async def get_my_dashboard(user_id: int = Query(...), db: Session = Depends(get_db)):
    results = db.query(UserProcedure).filter(UserProcedure.user_id == user_id).all()
    return [
        {
            "id": up.id,
            "title": up.title,
            "status": up.status,
            "completion": "30%"  # TODO: Calculate real progress
        }
        for up in results
    ]

# 4. API Cập nhật tiến độ
@router.patch("/dashboard/{procedure_id}")
async def update_dashboard(procedure_id: int, step: int = None, status: str = None, db: Session = Depends(get_db)):
    up = db.query(UserProcedure).filter(UserProcedure.id == procedure_id).first()
    if not up:
        raise HTTPException(status_code=404, detail="Not Found")
    if status:
        up.status = status
    # Optionally update step/progress in up.data
    db.commit()
    return {"status": "success", "message": "Đã cập nhật"}

# 5. API Xóa khỏi dashboard
@router.delete("/dashboard/{procedure_id}")
async def delete_dashboard(procedure_id: int, db: Session = Depends(get_db)):
    up = db.query(UserProcedure).filter(UserProcedure.id == procedure_id).first()
    if not up:
        raise HTTPException(status_code=404, detail="Not Found")
    db.delete(up)
    db.commit()
    return {"status": "success", "message": "Đã xóa khỏi dashboard"}
