import fitz
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from .models import DocumentMetadata, DocumentChunk
from .utils import log_error, log_info

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

