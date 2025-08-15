import fitz
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
import langextract as lx
import textwrap
from pypdf import PdfReader

from .config import config
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

def process_multiple_pdfs(files: List[UploadFile]) -> Dict[str, Any]:

    """Process multiple PDF files using LangExtract for hierarchical extraction"""
    all_documents = []
    all_chunks = []

    # Define prompt and example for structure extraction
    prompt = textwrap.dedent("""
        Extract section headers, subsections, and their hierarchy from the text. Provide exact text spans and parent-child relationships. For each section, include its level (1 for top-level, 2 for subsection, etc.), title, and parent section if applicable.
    """)
    examples = [
        lx.data.ExampleData(
            text="1. Introduction\nThis is the intro.\n1.1 Background\nDetails here.",
            extractions=[
                lx.data.Extraction(
                    extraction_class="section",
                    extraction_text="1. Introduction",
                    attributes={"level": 1, "title": "Introduction"}
                ),
                lx.data.Extraction(
                    extraction_class="section",
                    extraction_text="1.1 Background",
                    attributes={"level": 2, "title": "Background", "parent": "1. Introduction"}
                ),
            ]
        )
    ]

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

            # Use LangExtract for hierarchical extraction
            result = lx.extract(
                text_or_documents=text,
                prompt_description=prompt,
                examples=examples,
                model_id="gemini-2.5-flash",
                extraction_passes=1,
                max_workers=1,
                max_char_buffer=10000,
                api_key=config.GOOGLE_API_KEY
            )

            # Build chunks from LangExtract results
            chunks = []
            sorted_extractions = sorted(result.extractions, key=lambda e: e.char_interval.start_pos)
            
            for i, extraction in enumerate(sorted_extractions):
                if extraction.extraction_class == "section":
                    section_title = extraction.extraction_text
                    start_pos = extraction.char_interval.end_pos
                    
                    # Find the start of the next section, or use the end of the text
                    end_pos = len(text)
                    if i + 1 < len(sorted_extractions):
                        end_pos = sorted_extractions[i+1].char_interval.start_pos
                        
                    section_content = text[start_pos:end_pos].strip()
                    
                    # Create a chunk with both title and content
                    chunk_content = f"{section_title}\n\n{section_content}"
                    
                    chunk = DocumentChunk(
                        id=str(uuid.uuid4()),
                        document_id=doc_id,
                        content=chunk_content,
                        chunk_index=i,
                        page_number=1,  # Simplified
                        metadata={
                            "filename": file.filename,
                            "chunk_size": len(chunk_content),
                            "total_chunks": len(sorted_extractions),
                            "hierarchy_level": extraction.attributes.get("level"),
                            "parent_section": extraction.attributes.get("parent"),
                            "section_title": extraction.attributes.get("title"),
                            "structure_confidence": getattr(extraction, "confidence", 1.0),
                            "source_grounding": section_title  # Grounding is the title
                        }
                    )
                    chunks.append(chunk)

            doc_metadata.chunk_count = len(chunks)
            all_chunks.extend(chunks)
            all_documents.append(doc_metadata)
            log_info(f"Processed {file.filename} with LangExtract: {len(chunks)} chunks")

        except Exception as e:
            log_error(f"Error processing {file.filename}: {e}")
            continue

    return {
        "documents": all_documents,
        "chunks": all_chunks
    }