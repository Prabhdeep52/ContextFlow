import datetime
import time
import uuid
from fastapi import APIRouter, File, UploadFile , HTTPException
from .models import ConversationEntry, MetricsResponse, QuestionRequest, QuestionResponse, APIKeyRequest, APIKeyResponse
from .api_key_manager import configure_api_key, is_api_key_configured
from .memory_store import memory_store 
from .qa_chain import qa_chain
from .vector_store import vector_store
from typing import List
from .conversation_manager import conversation_manager
from .pdf_processing import process_multiple_pdfs
from .utils import calculate_cost, count_tokens, log_error

router = APIRouter()

# ============================================================================
# API ROUTES
# ============================================================================

@router.post("/upload")
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

@router.post("/ask")
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
        

        # Hierarchical search: get both section and chunk context
        search_results = vector_store.hierarchical_search(request.question, k_sections=2, k_chunks=request.top_k)
        relevant_docs = search_results["chunks"]
        section_context = "\n".join(f"Section: {s['section_title']} (score: {s['score']:.2f})" for s in search_results["sections"])

        if not relevant_docs:
            raise HTTPException(
                status_code=404,
                detail="No relevant documents found. Please upload some PDFs first."
            )

        # Generate answer with section context
        result = qa_chain.answer_question(request.question, relevant_docs, section_context=section_context)
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
            timestamp=datetime.datetime.now(),
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

@router.get("/documents")
async def get_documents():
    """Get list of uploaded documents"""
    return vector_store.get_document_summary()

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.datetime.now().isoformat()}

@router.post("/configure_api_key")
async def configure_api_key_endpoint(request: APIKeyRequest):
    """Configure the Google API key"""
    try:
        configure_api_key(request.api_key)
        
        # Reinitialize components after API key configuration
        from .api_key_manager import reinitialize_components
        reinitialize_components()
        
        return APIKeyResponse(
            message="API key configured successfully",
            configured=True
        )
    except Exception as e:
        log_error(f"API key configuration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api_key_status")
async def get_api_key_status():
    """Check if API key is configured"""
    return {
        "configured": is_api_key_configured(),
        "message": "API key is configured" if is_api_key_configured() else "API key not configured"
    }

@router.get("/history")
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

@router.delete("/history")
async def clear_conversation_history():
    """Clear conversation history"""
    conversation_manager.clear_history()
    return {"message": "Conversation history cleared"}

@router.get("/search")
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

@router.get("/metrics")
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

@router.get("/session_metrics")
async def get_session_metrics():
    """Get session-specific metrics"""
    return memory_store.get_session_metrics()
