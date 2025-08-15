import faiss
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import numpy as np
from typing import List, Dict, Any

from .models import DocumentChunk, DocumentMetadata
from .config import config
from .utils import log_error, log_info
from langchain_community.vectorstores import FAISS

# ============================================================================
# ENHANCED VECTOR STORE
# ============================================================================


class SimpleVectorStore:
    """Hierarchical vector store implementation with section-level and chunk-level search."""

    def __init__(self):
        self.documents = []
        self.chunks = []
        self.embeddings = None
        self.vector_store = None
        self.section_titles = set()
        self.section_to_chunks = {}  # section_title -> list of chunk indices

    def reset_embeddings(self):
        self.embeddings = None
        self.vector_store = None
        self.section_titles = set()
        self.section_to_chunks = {}

    def _initialize_embeddings(self):
        if not self.embeddings and config.GOOGLE_API_KEY:
            try:
                self.embeddings = GoogleGenerativeAIEmbeddings(
                    model=config.EMBEDDING_MODEL,
                    google_api_key=config.GOOGLE_API_KEY
                )
                log_info("Embeddings initialized")
                return True
            except Exception as e:
                log_error(f"Failed to initialize embeddings: {e}")
                return False
        return bool(self.embeddings)

    def add_documents(self, documents: List[DocumentMetadata], chunks: List[DocumentChunk]):
        self.documents.extend(documents)
        self.chunks.extend(chunks)

        # Build section index for hierarchical search
        for idx, chunk in enumerate(chunks):
            section_title = chunk.metadata.get("section_title")
            if section_title:
                self.section_titles.add(section_title)
                self.section_to_chunks.setdefault(section_title, []).append(len(self.chunks) - len(chunks) + idx)

        # Initialize embeddings if needed
        if not self._initialize_embeddings():
            log_error("Cannot add documents without embeddings")
            return

        # Create or update vector store
        if chunks:
            try:
                texts = [chunk.content for chunk in chunks]
                metadatas = [
                    {
                        "chunk_id": chunk.id,
                        "filename": chunk.metadata.get("filename", "Unknown"),
                        "document_id": chunk.document_id,
                        "section_title": chunk.metadata.get("section_title"),
                        "hierarchy_level": chunk.metadata.get("hierarchy_level"),
                        "parent_section": chunk.metadata.get("parent_section"),
                        "structure_confidence": chunk.metadata.get("structure_confidence"),
                        "source_grounding": chunk.metadata.get("source_grounding"),
                    }
                    for chunk in chunks
                ]

                if self.vector_store is None:
                    self.vector_store = FAISS.from_texts(texts, self.embeddings, metadatas=metadatas)
                else:
                    new_store = FAISS.from_texts(texts, self.embeddings, metadatas=metadatas)
                    self.vector_store.merge_from(new_store)

                log_info(f"Vector store updated with {len(chunks)} chunks")
            except Exception as e:
                log_error(f"Failed to create/update vector store: {e}")

    def search_sections(self, query: str, k: int = 3) -> list:
        """Search for relevant section titles using embeddings."""
        if not self.vector_store:
            log_error("Vector store not initialized")
            return []
        try:
            # Search all chunks, but only keep unique section titles
            results = self.vector_store.similarity_search_with_score(query, k=20)
            seen = set()
            section_results = []
            for doc, score in results:
                section_title = doc.metadata.get("section_title")
                if section_title and section_title not in seen:
                    section_results.append({
                        "section_title": section_title,
                        "score": float(score)
                    })
                    seen.add(section_title)
                if len(section_results) >= k:
                    break
            return section_results
        except Exception as e:
            log_error(f"Section search error: {e}")
            return []

    def search_chunks_in_section(self, section_title: str, query: str, k: int = 4) -> list:
        """Search for relevant chunks within a given section."""
        if not self.vector_store:
            log_error("Vector store not initialized")
            return []
        try:
            # Get indices of chunks in this section
            indices = self.section_to_chunks.get(section_title, [])
            if not indices:
                return []
            # Search all chunks, filter by section
            results = self.vector_store.similarity_search_with_score(query, k=20)
            filtered = []
            for doc, score in results:
                if doc.metadata.get("section_title") == section_title:
                    filtered.append({
                        "content": doc.page_content,
                        "score": float(score),
                        "filename": doc.metadata.get("filename", "Unknown"),
                        "chunk_id": doc.metadata.get("chunk_id", "Unknown"),
                        "section_title": section_title,
                        "hierarchy_level": doc.metadata.get("hierarchy_level"),
                        "parent_section": doc.metadata.get("parent_section"),
                        "structure_confidence": doc.metadata.get("structure_confidence"),
                        "source_grounding": doc.metadata.get("source_grounding"),
                    })
                if len(filtered) >= k:
                    break
            return filtered
        except Exception as e:
            log_error(f"Chunk-in-section search error: {e}")
            return []

    def hierarchical_search(self, query: str, k_sections: int = 2, k_chunks: int = 4) -> dict:
        """Hierarchical search: first find relevant sections, then top chunks in each."""
        section_results = self.search_sections(query, k=k_sections)
        all_chunks = []
        for section in section_results:
            section_title = section["section_title"]
            section_chunks = self.search_chunks_in_section(section_title, query, k=k_chunks)
            all_chunks.extend(section_chunks)
        return {
            "sections": section_results,
            "chunks": all_chunks
        }

    def search(self, query: str, k: int = 4, context: str = None, hierarchical: bool = False) -> list:
        """Search for relevant documents. If hierarchical=True, use section-level search first."""
        if hierarchical:
            results = self.hierarchical_search(query, k_sections=2, k_chunks=k)
            return results["chunks"]
        if not self.vector_store:
            log_error("Vector store not initialized")
            return []
        try:
            enhanced_query = query
            if context:
                enhanced_query = f"Context: {context}\nQuestion: {query}"
            results = self.vector_store.similarity_search_with_score(enhanced_query, k=k)
            return [
                {
                    "content": doc.page_content,
                    "score": float(score),
                    "filename": doc.metadata.get("filename", "Unknown"),
                    "chunk_id": doc.metadata.get("chunk_id", "Unknown"),
                    "section_title": doc.metadata.get("section_title"),
                    "hierarchy_level": doc.metadata.get("hierarchy_level"),
                    "parent_section": doc.metadata.get("parent_section"),
                    "structure_confidence": doc.metadata.get("structure_confidence"),
                    "source_grounding": doc.metadata.get("source_grounding"),
                }
                for doc, score in results
            ]
        except Exception as e:
            log_error(f"Search error: {e}")
            return []

    def get_document_summary(self) -> Dict[str, Any]:
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