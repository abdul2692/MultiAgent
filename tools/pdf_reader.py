"""
PDF Processing Tool for Multi-Agent Research Assistant.
Uses PyMuPDF (fitz) for fast, 100% local, zero-budget document parsing.
"""
import os
import sys
import logging
from typing import List

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pymupdf  # Modern PyMuPDF API
from models.schemas import DocumentChunk

logger = logging.getLogger("multi_agent.tools.pdf_reader")

def extract_pdf_chunks(pdf_path: str, max_chars_per_chunk: int = 1200) -> List[DocumentChunk]:
    """
    Extracts text chunks with page number citations from a local PDF document.
    
    Args:
        pdf_path: Absolute or relative path to the PDF file.
        max_chars_per_chunk: Approximate character limit per chunk for clean context windows.
        
    Returns:
        List of DocumentChunk objects with file name, page number, and text content.
    """
    chunks: List[DocumentChunk] = []
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found at path: {pdf_path}")
        return chunks
        
    file_name = os.path.basename(pdf_path)
    logger.info(f"Opening and parsing PDF: {file_name}")
    
    try:
        doc = pymupdf.open(pdf_path)
        total_pages = len(doc)
        for page_idx in range(total_pages):
            page_num = page_idx + 1  # 1-based page numbering for human citations
            page = doc[page_idx]
            page_text = page.get_text("text").strip()
            
            if not page_text:
                continue
                
            # If the page text is longer than max_chars_per_chunk, split gracefully into paragraphs
            if len(page_text) > max_chars_per_chunk:
                paragraphs = page_text.split("\n\n")
                current_chunk = ""
                
                for para in paragraphs:
                    if len(current_chunk) + len(para) > max_chars_per_chunk:
                        if current_chunk.strip():
                            chunks.append(
                                DocumentChunk(
                                    file_name=file_name,
                                    page_number=page_num,
                                    text=current_chunk.strip()
                                )
                            )
                        current_chunk = para + "\n\n"
                    else:
                        current_chunk += para + "\n\n"
                        
                if current_chunk.strip():
                    chunks.append(
                        DocumentChunk(
                            file_name=file_name,
                            page_number=page_num,
                            text=current_chunk.strip()
                        )
                    )
            else:
                chunks.append(
                    DocumentChunk(
                        file_name=file_name,
                        page_number=page_num,
                        text=page_text
                    )
                )
                
        doc.close()
        logger.info(f"Extracted {len(chunks)} chunks across {total_pages} pages from {file_name}")
    except Exception as e:
        logger.error(f"Error parsing PDF '{file_name}': {e}", exc_info=True)
        
    return chunks

if __name__ == "__main__":
    # Self-test: create a dummy test PDF using PyMuPDF to test extraction
    test_pdf_path = os.path.join(os.path.dirname(__file__), "sample_test.pdf")
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 72), "Multi-Agent Systems Research Paper\n\nPage 1 Content: Solid-state electrolytes.")
    doc.save(test_pdf_path)
    doc.close()

    print("Testing PDF Reader Tool...")
    results = extract_pdf_chunks(test_pdf_path)
    for c in results:
        print(f"File: {c.file_name} | Page: {c.page_number} | Text: {c.text}")

    if os.path.exists(test_pdf_path):
        os.remove(test_pdf_path)
