"""
Agent 2: Reader Agent.
Responsible for:
1. Ingesting local PDF documents.
2. Extracting text chunks with page number tracking.
3. Identifying key facts, claims, and data points.
4. Preserving page citations in ReaderOutput.
"""
import os
import sys
import logging
from typing import List

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from models.schemas import ReaderOutput, DocumentChunk
from tools.pdf_reader import extract_pdf_chunks
from utils.ollama_manager import ensure_ollama_running

logger = logging.getLogger("multi_agent.agents.reader")

def get_llm(temperature: float = 0.2):
    ensure_ollama_running()
    return ChatOllama(
        model=os.getenv("OLLAMA_MODEL", "llama3.2:1b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        temperature=temperature
    )

def run_reader(pdf_paths: List[str]) -> ReaderOutput:
    """
    Orchestrates the Reader Agent:
    1. Extracts chunks from all provided PDF documents.
    2. Identifies key facts and synthesizes content with citations.
    """
    logger.info(f"[Agent 2: Reader] Processing {len(pdf_paths)} documents...")
    
    if not pdf_paths:
        logger.info("No documents provided to Reader. Returning empty ReaderOutput.")
        return ReaderOutput(
            documents_read=[],
            chunks=[],
            document_summary="No local documents were provided for this research session.",
            key_facts=[]
        )
        
    all_chunks: List[DocumentChunk] = []
    documents_read: List[str] = []
    
    for path in pdf_paths:
        if os.path.exists(path):
            extracted = extract_pdf_chunks(path)
            all_chunks.extend(extracted)
            documents_read.append(os.path.basename(path))
            
    if not all_chunks:
        return ReaderOutput(
            documents_read=documents_read,
            chunks=[],
            document_summary="Documents were provided, but no extractable text was found.",
            key_facts=[]
        )
        
    llm = get_llm()
    
    # Format chunks with page numbers for the LLM
    formatted_chunks = "\n\n".join([
        f"--- Document: {c.file_name} (Page {c.page_number}) ---\n{c.text}"
        for c in all_chunks[:8]  # Limit to 8 chunks to keep prompt clean for 1B model
    ])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are an Academic Document Analyst. Read the document passages provided. "
            "Extract the top key factual findings, referencing the specific page numbers. "
            "Format the output as:\n"
            "SUMMARY: <2-3 sentence overview of document findings>\n"
            "KEY FACTS:\n"
            "- <Fact 1> [DocName, p. X]\n"
            "- <Fact 2> [DocName, p. Y]"
        )),
        ("human", "Extracted Document Passages:\n{passages}")
    ])
    
    document_summary = ""
    key_facts: List[str] = []
    
    try:
        chain = prompt | llm
        resp = chain.invoke({"passages": formatted_chunks})
        content = resp.content.strip()
        
        # Parse the structured response
        if "KEY FACTS:" in content:
            parts = content.split("KEY FACTS:")
            summary_part = parts[0].replace("SUMMARY:", "").strip()
            facts_part = parts[1].strip()
            document_summary = summary_part
            key_facts = [f.strip().lstrip("-* ") for f in facts_part.split("\n") if f.strip()]
        else:
            document_summary = content
            key_facts = [f"Data extracted from {d}" for d in documents_read]
            
    except Exception as e:
        logger.warning(f"LLM document analysis failed: {e}. Falling back to baseline.")
        document_summary = f"Processed {len(all_chunks)} passages across {len(documents_read)} documents."
        key_facts = [f"Extracted passage from {c.file_name} (Page {c.page_number})" for c in all_chunks[:3]]
        
    return ReaderOutput(
        documents_read=documents_read,
        chunks=all_chunks,
        document_summary=document_summary,
        key_facts=key_facts
    )

if __name__ == "__main__":
    print("Testing Reader Agent...")
    # Test with empty documents (graceful pass)
    res_empty = run_reader([])
    print("Empty pass summary:", res_empty.document_summary)
