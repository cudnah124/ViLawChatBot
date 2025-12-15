
from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class DocumentMetadata(Base):
    __tablename__ = "document_metadata"
    id = Column(Integer, primary_key=True)
    external_id = Column(String, nullable=True)  # ID file từ hệ thống ngoài (nếu có)
    filename = Column(String, nullable=True)     # Tên file gốc (không bắt buộc)
    filetype = Column(String, nullable=True)     # Loại file (pdf, jpg, ...)
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ocr_text = Column(String, nullable=False)    # Nội dung text đã OCR
    created_at = Column(String)                  # ISO format hoặc DateTime
    conversation_id = Column(String, ForeignKey("conversations.conversation_id"), nullable=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)

# Bảng users mẫu
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)

class UserProcedure(Base):
    __tablename__ = "user_procedures"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    status = Column(String)  # "In Progress", "Completed"
    data = Column(JSON)      # Lưu toàn bộ cấu trúc các bước và checklist dưới dạng JSON

class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question = Column(String)
    answer = Column(String)
    timestamp = Column(String)  # ISO format, hoặc dùng DateTime nếu muốn

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True)
    conversation_id = Column(String, unique=True, nullable=False)  # UUID or similar
    account_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String)
    created_at = Column(String)  # ISO format or DateTime

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    conversation_id = Column(String, ForeignKey("conversations.conversation_id"), nullable=False)
    role = Column(String)  # 'system', 'user', 'assistant'
    content = Column(String)
    timestamp = Column(String)  # ISO format or DateTime
