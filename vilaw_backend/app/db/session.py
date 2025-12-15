import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base

# Đọc DATABASE_URL từ biến môi trường (Render sẽ inject biến này)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/vilaw_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
