class DocumentMetadataResponse(BaseModel):
    id: int
    external_id: Optional[str]
    filename: Optional[str]
    filetype: Optional[str]
    uploader_id: Optional[int]
    ocr_text: str
    created_at: Optional[str]
    conversation_id: Optional[str]
    message_id: Optional[int]
from typing import List, Optional
from pydantic import BaseModel

class Clause(BaseModel):
    number: Optional[str]
    text: str

class Entity(BaseModel):
    role: str
    name: str

class DocumentAnalysisResponse(BaseModel):
    filename: str
    file_hash: str
    blockchain_status: str
    document_type: str
    entities: List[Entity]
    clauses: List[Clause]
    handwritten_notes: Optional[str] = None
