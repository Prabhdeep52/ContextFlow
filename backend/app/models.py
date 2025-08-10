from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Any

class QuestionRequest(BaseModel):
    question: str
    top_k: int = 4
    include_context: bool = False
    context_length: int = 3

class QuestionResponse(BaseModel):
    answer: str
    sources: List[str]
    processing_time: float
    total_tokens: int
    cost: float

class DocumentMetadata(BaseModel):
    id: str
    filename: str
    upload_date: datetime
    file_size: int
    page_count: int
    chunk_count: int

class DocumentChunk(BaseModel):
    id: str
    document_id: str
    content: str
    chunk_index: int
    page_number: int
    metadata: Dict[str, Any]

class ConversationEntry(BaseModel):
    id: str
    question: str
    answer: str
    timestamp: datetime
    sources: List[str]
    processing_time: float
    total_tokens: int
    cost: float

class APIKeyRequest(BaseModel):
    api_key: str

class APIKeyResponse(BaseModel):
    message: str
    configured: bool

class SearchRequest(BaseModel):
    q: str
    limit: int = 10

class MetricsResponse(BaseModel):
    total_documents: int
    total_chunks: int
    total_conversations: int
    total_tokens_processed: int
    total_cost: float