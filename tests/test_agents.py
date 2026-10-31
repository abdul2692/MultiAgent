"""
Unit and Integration Test Suite for Multi-Agent System.
Verifies all agents, tools, schemas, and metrics with Pytest.
"""
import os
import sys
import pytest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.schemas import (
    WebSearchResult,
    ResearcherOutput,
    DocumentChunk,
    ReaderOutput,
    AnalystOutput,
    ResearchReport
)
from tools.web_search import search_web
from tools.pdf_reader import extract_pdf_chunks
from tools.report_generator import export_to_markdown, export_to_pdf
from utils.metrics import MetricsTracker
from graph.workflow import create_research_graph
import pymupdf

def test_schemas():
    """Validates Pydantic data schemas."""
    res = WebSearchResult(title="Test", url="https://example.com", snippet="Example text")
    assert res.title == "Test"
    assert res.url == "https://example.com"
    
    chunk = DocumentChunk(file_name="paper.pdf", page_number=1, text="Sample paragraph")
    assert chunk.page_number == 1

def test_web_search():
    """Verifies free web search tool functionality."""
    results = search_web("Python programming language", max_results=2)
    assert isinstance(results, list)
    assert len(results) > 0
    assert hasattr(results[0], "title")
    assert hasattr(results[0], "url")
    assert hasattr(results[0], "snippet")

def test_pdf_extraction(tmp_path):
    """Verifies PyMuPDF local document text chunking."""
    test_pdf = tmp_path / "test_doc.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 72), "Multi-Agent Research Assistant Unit Test Text.")
    doc.save(str(test_pdf))
    doc.close()

    chunks = extract_pdf_chunks(str(test_pdf))
    assert len(chunks) == 1
    assert chunks[0].page_number == 1
    assert "Multi-Agent" in chunks[0].text

def test_report_export(tmp_path):
    """Verifies Markdown and PDF export generation."""
    report = ResearchReport(
        title="Pytest Generated Briefing",
        executive_summary="Executive summary body.",
        methodology="Automated LangGraph verification.",
        findings="Verified findings.",
        analysis="Technical analysis section.",
        conclusion="Final strategic conclusion.",
        references=["[1] https://example.com/test — Reference 1"]
    )
    
    md_path = export_to_markdown(report, "pytest_report")
    pdf_path = export_to_pdf(report, "pytest_report")
    
    assert os.path.exists(md_path)
    assert os.path.exists(pdf_path)
    assert os.path.getsize(md_path) > 50
    assert os.path.getsize(pdf_path) > 500

    # Clean up
    os.remove(md_path)
    os.remove(pdf_path)

def test_metrics_tracker(tmp_path):
    """Verifies metrics tracking and calculation from actual executions."""
    metrics_file = str(tmp_path / "test_metrics.json")
    t = MetricsTracker(storage_path=metrics_file)
    
    summary = t.record_run(
        topic="AI Ethics",
        duration_seconds=12.5,
        success=True,
        sources_count=5,
        agent_statuses={"researcher": "done", "writer": "done"}
    )
    
    assert summary["total_tasks"] == 1
    assert summary["successful_tasks"] == 1
    assert summary["avg_execution_time_seconds"] == 12.5
    assert summary["total_sources_collected"] == 5
    assert summary["total_cost_inr"] == 0.0

def test_workflow_graph_compilation():
    """Verifies LangGraph StateGraph builds and compiles without errors."""
    app = create_research_graph()
    assert app is not None
    # Check that nodes are registered in the graph
    node_keys = list(app.get_graph().nodes.keys())
    assert "researcher" in node_keys
    assert "reader" in node_keys
    assert "analyst" in node_keys
    assert "writer" in node_keys

