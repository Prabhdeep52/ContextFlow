import faiss
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import numpy as np
from typing import List, Dict, Any

from pydot import Any
from .models import DocumentChunk, DocumentMetadata
from .config import EMBEDDING_MODEL, GOOGLE_API_KEY
from .utils import log_error, log_info
from langchain_community.vectorstores import FAISS

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
                    new_store = faiss.from_texts(texts, self.embeddings, metadatas=metadatas)
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