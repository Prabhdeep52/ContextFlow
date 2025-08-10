"""
Consolidated RAG Pipeline Application
All logic in one file to eliminate import errors
"""

import os
import json
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pypdf import PdfReader
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.schema import Document

# ============================================================================
# CONFIGURATION
# ============================================================================

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# Updated to use the correct model name
CHAT_MODEL = "gemini-1.5-flash"
EMBEDDING_MODEL = "models/embedding-001"
TEMPERATURE = 0.1

# Pricing configuration
PRICING = {
    "input_tokens_per_1k": 0.0005,
    "output_tokens_per_1k": 0.0015,
    "embedding_per_1k": 0.0001
}

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

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

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def log_info(message: str):
    """Simple logging function"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] INFO: {message}")

def log_error(message: str):
    """Simple error logging function"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] ERROR: {message}")

def count_tokens(text: str) -> int:
    """Simple token counting (approximate)"""
    return int(len(text.split()) * 1.3)  # Rough approximation

def calculate_cost(input_tokens: int, output_tokens: int, embedding_tokens: int = 0) -> float:
    """Calculate API cost"""
    input_cost = (input_tokens / 1000) * PRICING["input_tokens_per_1k"]
    output_cost = (output_tokens / 1000) * PRICING["output_tokens_per_1k"]
    embedding_cost = (embedding_tokens / 1000) * PRICING["embedding_per_1k"]
    return input_cost + output_cost + embedding_cost

# ============================================================================
# PDF PROCESSING
# ============================================================================

def get_pdf_text(pdf_file_object) -> str:
    """Extract text from PDF file"""
    try:
        pdf_reader = PdfReader(pdf_file_object)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        log_error(f"Error reading PDF: {e}")
        raise HTTPException(status_code=400, detail=f"Error reading PDF: {str(e)}")

def get_text_chunks(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """Split text into chunks"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    chunks = text_splitter.split_text(text)
    return chunks

def process_multiple_pdfs(files: List[UploadFile]) -> Dict[str, Any]:
    """Process multiple PDF files"""
    all_documents = []
    all_chunks = []
    
    for file in files:
        try:
            # Extract text
            text = get_pdf_text(file.file)
            
            if not text.strip():
                log_error(f"No text extracted from {file.filename}")
                continue
            
            # Create document metadata
            doc_id = str(uuid.uuid4())
            doc_metadata = DocumentMetadata(
                id=doc_id,
                filename=file.filename,
                upload_date=datetime.now(),
                file_size=len(text),
                page_count=1,  # Simplified
                chunk_count=0
            )
            
            # Split into chunks
            chunks = get_text_chunks(text)
            doc_metadata.chunk_count = len(chunks)
            
            # Create chunk objects
            for i, chunk_text in enumerate(chunks):
                chunk = DocumentChunk(
                    id=str(uuid.uuid4()),
                    document_id=doc_id,
                    content=chunk_text,
                    chunk_index=i,
                    page_number=1,  # Simplified
                    metadata={
                        "filename": file.filename,
                        "chunk_size": len(chunk_text),
                        "total_chunks": len(chunks)
                    }
                )
                all_chunks.append(chunk)
            
            all_documents.append(doc_metadata)
            log_info(f"Processed {file.filename}: {len(chunks)} chunks")
            
        except Exception as e:
            log_error(f"Error processing {file.filename}: {e}")
            continue
    
    return {
        "documents": all_documents,
        "chunks": all_chunks
    }

# ============================================================================
# STORAGE AND STATE MANAGEMENT
# ============================================================================

class ConversationManager:
    """Manages conversation history"""
    
    def __init__(self):
        self.conversations: List[ConversationEntry] = []
    
    def add_conversation(self, entry: ConversationEntry):
        """Add a new conversation entry"""
        self.conversations.append(entry)
        # Keep only last 100 conversations
        if len(self.conversations) > 100:
            self.conversations = self.conversations[-100:]
    
    def get_conversation_history(self, limit: int = 10) -> List[ConversationEntry]:
        """Get conversation history"""
        return self.conversations[-limit:] if self.conversations else []
    
    def get_conversation_context(self, context_length: int = 3) -> str:
        """Get conversation context for enhanced retrieval"""
        recent = self.get_conversation_history(context_length)
        if not recent:
            return ""
        
        context = "Recent conversation context:\n"
        for conv in recent:
            context += f"Q: {conv.question}\nA: {conv.answer}\n\n"
        return context
    
    def search_conversations(self, query: str, limit: int = 10) -> List[ConversationEntry]:
        """Search through conversation history"""
        query_lower = query.lower()
        results = []
        
        for conv in reversed(self.conversations):
            if (query_lower in conv.question.lower() or 
                query_lower in conv.answer.lower()):
                results.append(conv)
                if len(results) >= limit:
                    break
        
        return results
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversations.clear()

class MemoryStore:
    """Stores metrics and session data"""
    
    def __init__(self):
        self.total_tokens_processed = 0
        self.total_cost = 0.0
        self.session_start = datetime.now()
    
    def add_metrics(self, tokens: int, cost: float):
        """Add metrics to the store"""
        self.total_tokens_processed += tokens
        self.total_cost += cost
    
    def get_session_metrics(self) -> Dict[str, Any]:
        """Get session metrics"""
        session_duration = (datetime.now() - self.session_start).total_seconds()
        return {
            "session_duration": session_duration,
            "total_tokens_processed": self.total_tokens_processed,
            "total_cost": self.total_cost,
            "tokens_per_minute": (self.total_tokens_processed / (session_duration / 60)) if session_duration > 0 else 0
        }

# Global instances
conversation_manager = ConversationManager()
memory_store = MemoryStore()

# ============================================================================
# API KEY MANAGEMENT
# ============================================================================

def configure_api_key(api_key: str):
    """Configure the Google API key"""
    global GOOGLE_API_KEY
    GOOGLE_API_KEY = api_key
    os.environ["GOOGLE_API_KEY"] = api_key  # Set environment variable too
    log_info("API key configured")
    
    # Reinitialize components
    try:
        qa_chain.reset()
        vector_store.reset_embeddings()
        log_info("Components reinitialized with new API key")
    except Exception as e:
        log_error(f"Failed to reinitialize components: {e}")

def is_api_key_configured() -> bool:
    """Check if API key is configured"""
    return bool(GOOGLE_API_KEY)

# ============================================================================
# ENHANCED VECTOR STORE
# ============================================================================

class SimpleVectorStore:
    """Simplified vector store implementation"""
    
    def __init__(self):
        self.documents = []
        self.chunks = []
        self.embeddings = None
        self.vector_store = None
        
    def reset_embeddings(self):
        """Reset embeddings to force reinitialization"""
        self.embeddings = None
        self.vector_store = None
        
    def _initialize_embeddings(self):
        """Initialize embeddings if not done"""
        if not self.embeddings and GOOGLE_API_KEY:
            try:
                self.embeddings = GoogleGenerativeAIEmbeddings(
                    model=EMBEDDING_MODEL,
                    google_api_key=GOOGLE_API_KEY
                )
                log_info("Embeddings initialized")
                return True
            except Exception as e:
                log_error(f"Failed to initialize embeddings: {e}")
                return False
        return bool(self.embeddings)
        
    def add_documents(self, documents: List[DocumentMetadata], chunks: List[DocumentChunk]):
        """Add documents to the store"""
        self.documents.extend(documents)
        self.chunks.extend(chunks)
        
        # Initialize embeddings if needed
        if not self._initialize_embeddings():
            log_error("Cannot add documents without embeddings")
            return
        
        # Create simple vector store
        if chunks:
            try:
                texts = [chunk.content for chunk in chunks]
                metadatas = [
                    {
                        "chunk_id": chunk.id, 
                        "filename": chunk.metadata.get("filename", "Unknown"),
                        "document_id": chunk.document_id
                    } 
                    for chunk in chunks
                ]
                
                if self.vector_store is None:
                    self.vector_store = FAISS.from_texts(texts, self.embeddings, metadatas=metadatas)
                else:
                    # Add to existing vector store
                    new_store = FAISS.from_texts(texts, self.embeddings, metadatas=metadatas)
                    self.vector_store.merge_from(new_store)
                    
                log_info(f"Vector store updated with {len(chunks)} chunks")
            except Exception as e:
                log_error(f"Failed to create/update vector store: {e}")
    
    def search(self, query: str, k: int = 4, context: str = None) -> List[Dict[str, Any]]:
        """Search for relevant documents with optional context"""
        if not self.vector_store:
            log_error("Vector store not initialized")
            return []
        
        try:
            # Enhance query with context if provided
            enhanced_query = query
            if context:
                enhanced_query = f"Context: {context}\nQuestion: {query}"
            
            results = self.vector_store.similarity_search_with_score(enhanced_query, k=k)
            return [
                {
                    "content": doc.page_content,
                    "score": float(score),
                    "filename": doc.metadata.get("filename", "Unknown"),
                    "chunk_id": doc.metadata.get("chunk_id", "Unknown")
                }
                for doc, score in results
            ]
        except Exception as e:
            log_error(f"Search error: {e}")
            return []
    
    def get_document_summary(self) -> Dict[str, Any]:
        """Get summary of all documents"""
        if not self.documents:
            return {"total_documents": 0, "total_chunks": 0, "documents": []}
        
        total_chunks = sum(doc.chunk_count for doc in self.documents)
        return {
            "total_documents": len(self.documents),
            "total_chunks": total_chunks,
            "documents": [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "upload_date": doc.upload_date,
                    "chunk_count": doc.chunk_count
                }
                for doc in self.documents
            ]
        }

# Global vector store instance
vector_store = SimpleVectorStore()

# ============================================================================
# ENHANCED QA CHAIN
# ============================================================================

class SimpleQAChain:
    """Simplified QA chain implementation"""
    
    def __init__(self):
        self.model = None
        self.chain = None
        
    def reset(self):
        """Reset the model and chain"""
        self.model = None
        self.chain = None
        
    def _initialize(self):
        """Initialize the model and chain"""
        if not GOOGLE_API_KEY:
            raise ValueError("Google API key not configured")
        
        if self.model is None:
            try:
                self.model = ChatGoogleGenerativeAI(
                    model=CHAT_MODEL,
                    temperature=TEMPERATURE,
                    google_api_key=GOOGLE_API_KEY
                )
                log_info(f"Model initialized: {CHAT_MODEL}")
            except Exception as e:
                log_error(f"Failed to initialize model: {e}")
                raise
        
        if self.chain is None:
            try:
                # Create simple QA chain
                prompt_template = """
                You are a helpful assistant that answers questions based on the provided context.
                Please provide accurate and helpful answers based solely on the given context.
                If the answer is not in the context, please say so clearly.
                
                Context: {context}
                
                Question: {question}
                
                Answer:"""
                
                prompt = PromptTemplate(
                    template=prompt_template,
                    input_variables=["context", "question"]
                )
                
                self.chain = load_qa_chain(
                    self.model,
                    chain_type="stuff",
                    prompt=prompt
                )
                
                log_info("QA chain initialized")
                
            except Exception as e:
                log_error(f"Failed to initialize QA chain: {e}")
                raise
    
    def answer_question(self, question: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Answer a question using the provided documents"""
        try:
            self._initialize()
            
            # Prepare input for the chain - create proper Document objects
            input_docs = [
                Document(
                    page_content=doc["content"],
                    metadata={
                        "filename": doc.get("filename", "Unknown"),
                        "chunk_id": doc.get("chunk_id", "Unknown")
                    }
                ) 
                for doc in documents
            ]
            
            result = self.chain.invoke({
                "input_documents": input_docs,
                "question": question
            })
            
            return result
            
        except Exception as e:
            log_error(f"Error answering question: {e}")
            raise

# Global QA chain instance
qa_chain = SimpleQAChain()

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(title="RAG Pipeline", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# API ROUTES
# ============================================================================

@app.post("/upload")
async def upload_pdfs(files: List[UploadFile] = File(...)):
    """Upload and process PDF files"""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    if not is_api_key_configured():
        raise HTTPException(status_code=400, detail="API key not configured. Please configure it first.")
    
    try:
        # Process PDFs
        result = process_multiple_pdfs(files)
        
        if not result["documents"]:
            raise HTTPException(status_code=400, detail="No valid documents could be processed")
        
        # Add to vector store
        vector_store.add_documents(result["documents"], result["chunks"])
        
        return {
            "message": f"Successfully processed {len(result['documents'])} PDF(s)",
            "documents": len(result["documents"]),
            "chunks": len(result["chunks"])
        }
        
    except Exception as e:
        log_error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
async def ask_question(request: QuestionRequest):
    """Ask a question about the uploaded documents"""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    if not is_api_key_configured():
        raise HTTPException(status_code=400, detail="API key not configured. Please configure it first.")
    
    try:
        start_time = time.time()
        
        # Get context from conversation history if requested
        context = ""
        if request.include_context:
            context = conversation_manager.get_conversation_context(request.context_length)
        
        # Search for relevant documents
        relevant_docs = vector_store.search(request.question, request.top_k, context)
        
        if not relevant_docs:
            raise HTTPException(
                status_code=404,
                detail="No relevant documents found. Please upload some PDFs first."
            )
        
        # Generate answer
        result = qa_chain.answer_question(request.question, relevant_docs)
        answer = result.get("output_text", result.get("answer", str(result)))
        
        # Calculate metrics
        processing_time = time.time() - start_time
        question_tokens = count_tokens(request.question)
        context_tokens = sum(count_tokens(doc["content"]) for doc in relevant_docs)
        answer_tokens = count_tokens(answer)
        total_tokens = question_tokens + context_tokens + answer_tokens
        
        # Calculate cost
        cost = calculate_cost(question_tokens + context_tokens, answer_tokens)
        
        # Extract sources
        sources = list(set(doc["filename"] for doc in relevant_docs))
        
        # Store conversation
        conversation_entry = ConversationEntry(
            id=str(uuid.uuid4()),
            question=request.question,
            answer=answer,
            timestamp=datetime.now(),
            sources=sources,
            processing_time=processing_time,
            total_tokens=total_tokens,
            cost=cost
        )
        conversation_manager.add_conversation(conversation_entry)
        
        # Update metrics
        memory_store.add_metrics(total_tokens, cost)
        
        return QuestionResponse(
            answer=answer,
            sources=sources,
            processing_time=processing_time,
            total_tokens=total_tokens,
            cost=cost
        )
        
    except Exception as e:
        log_error(f"Question error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
async def get_documents():
    """Get list of uploaded documents"""
    return vector_store.get_document_summary()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/configure_api_key")
async def configure_api_key_endpoint(request: APIKeyRequest):
    """Configure the Google API key"""
    try:
        configure_api_key(request.api_key)
        return APIKeyResponse(
            message="API key configured successfully",
            configured=True
        )
    except Exception as e:
        log_error(f"API key configuration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api_key_status")
async def get_api_key_status():
    """Check if API key is configured"""
    return {
        "configured": is_api_key_configured(),
        "message": "API key is configured" if is_api_key_configured() else "API key not configured"
    }

@app.get("/history")
async def get_conversation_history(limit: int = 10):
    """Get conversation history"""
    history = conversation_manager.get_conversation_history(limit)
    return {
        "conversations": [
            {
                "id": conv.id,
                "question": conv.question,
                "answer": conv.answer,
                "timestamp": conv.timestamp.isoformat(),
                "sources": conv.sources,
                "processing_time": conv.processing_time,
                "total_tokens": conv.total_tokens,
                "cost": conv.cost
            }
            for conv in history
        ],
        "total": len(history)
    }

@app.delete("/history")
async def clear_conversation_history():
    """Clear conversation history"""
    conversation_manager.clear_history()
    return {"message": "Conversation history cleared"}

@app.get("/search")
async def search_conversations(q: str, limit: int = 10):
    """Search through conversation history"""
    results = conversation_manager.search_conversations(q, limit)
    return {
        "query": q,
        "results": [
            {
                "id": conv.id,
                "question": conv.question,
                "answer": conv.answer,
                "timestamp": conv.timestamp.isoformat(),
                "sources": conv.sources
            }
            for conv in results
        ],
        "total": len(results)
    }

@app.get("/metrics")
async def get_metrics():
    """Get system metrics"""
    session_metrics = memory_store.get_session_metrics()
    doc_summary = vector_store.get_document_summary()
    
    return MetricsResponse(
        total_documents=doc_summary["total_documents"],
        total_chunks=doc_summary["total_chunks"],
        total_conversations=len(conversation_manager.conversations),
        total_tokens_processed=session_metrics["total_tokens_processed"],
        total_cost=session_metrics["total_cost"]
    )

@app.get("/session_metrics")
async def get_session_metrics():
    """Get session-specific metrics"""
    return memory_store.get_session_metrics()

# Initialize with environment API key if available
if GOOGLE_API_KEY:
    log_info("API key found in environment")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    log_info("Starting RAG Pipeline server...")
    log_info(f"Using model: {CHAT_MODEL}")
    log_info(f"Using embedding model: {EMBEDDING_MODEL}")
    uvicorn.run(app, host="0.0.0.0", port=8000)  # Make sure this is 8000, not 3000