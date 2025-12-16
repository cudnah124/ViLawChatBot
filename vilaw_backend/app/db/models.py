from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Text, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

# -------------------------------------------------------------------
# 1. BẢNG QUẢN LÝ VĂN BẢN LUẬT (Metadata)
# -------------------------------------------------------------------
class LawDocument(Base):
    __tablename__ = "law_documents"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)        # VD: Bộ luật Dân sự 2015
    code_number = Column(String, nullable=True)  # VD: 91/2015/QH13
    issuing_authority = Column(String)           # VD: Quốc hội
    effective_date = Column(String)              # Ngày hiệu lực
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Quan hệ 1-N với các đoạn văn bản (chunks)
    chunks = relationship("LawChunk", back_populates="document", cascade="all, delete-orphan")

# -------------------------------------------------------------------
# 2. BẢNG LƯU ĐIỀU KHOẢN (Dữ liệu cho RAG tìm kiếm)
# -------------------------------------------------------------------
class LawChunk(Base):
    __tablename__ = "law_chunks"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("law_documents.id"), nullable=False)
    title = Column(String, nullable=False)       # VD: Điều 1 - Phạm vi điều chỉnh
    content = Column(Text, nullable=False)       # Nội dung chi tiết của điều luật

    __table_args__ = (
        UniqueConstraint('document_id', 'title', name='uq_document_title'),
        {'sqlite_autoincrement': True},
    )

    # Quan hệ ngược lại để biết đoạn này thuộc luật nào
    document = relationship("LawDocument", back_populates="chunks")

# -------------------------------------------------------------------
# 3. CÁC BẢNG KHÁC (USER, CHAT...)
# -------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)

# Bảng lưu file OCR user upload tạm thời (Không dùng cho Knowledge Base)
class OCRDocument(Base):
    __tablename__ = "ocr_documents"
    id = Column(Integer, primary_key=True)
    filename = Column(String)
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ocr_text = Column(Text) # Dùng Text thay vì String để chứa văn bản dài
    created_at = Column(DateTime, default=datetime.utcnow)


# Bảng lưu các thủ tục mà user theo dõi (Dashboard)
class UserProcedure(Base):
    __tablename__ = "user_procedures"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    status = Column(String, default="In Progress")
    data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question = Column(Text)
    answer = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)