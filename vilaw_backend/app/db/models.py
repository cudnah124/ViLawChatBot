from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Text, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class LawDocument(Base):
    __tablename__ = "law_documents"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    code_number = Column(String, nullable=True)
    issuing_authority = Column(String)
    effective_date = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    chunks = relationship("LawChunk", back_populates="document", cascade="all, delete-orphan")


class LawChunk(Base):
    __tablename__ = "law_chunks"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("law_documents.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)

    __table_args__ = (
        UniqueConstraint('document_id', 'title', name='uq_document_title'),
        {'sqlite_autoincrement': True},
    )

    document = relationship("LawDocument", back_populates="chunks")



class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)


class OCRDocument(Base):
    __tablename__ = "ocr_documents"
    id = Column(Integer, primary_key=True)
    filename = Column(String)
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ocr_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)



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