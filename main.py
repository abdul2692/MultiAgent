"""
Command Line Interface (CLI) for Multi-Agent Research Assistant.
Usage:
    python main.py --topic "Artificial Intelligence in Healthcare"
    python main.py --topic "Solid-State Batteries" --pdf paper.pdf
"""
import os
import sys
import time
import argparse
import logging

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from graph.workflow import create_research_graph
from graph.state import ResearchState
from tools.report_generator import export_to_markdown, export_to_pdf
from utils.metrics import tracker
from utils.logger import setup_logger
from utils.ollama_manager import ensure_ollama_running

logger = setup_logger("multi_agent.cli")

def run_pipeline(topic: str, pdf_paths: list = None) -> dict:
    """Executes the complete multi-agent pipeline and records execution metrics."""
    if pdf_paths is None:
        pdf_paths = []

    print("\n" + "=" * 60)
    print(f"🚀 MULTI-AGENT RESEARCH ASSISTANT (₹0 BUDGET)")
    print(f"📌 Topic: {topic}")
    if pdf_paths:
        print(f"📄 Attached PDFs: {', '.join(pdf_paths)}")
    print("=" * 60 + "\n")

    ensure_ollama_running()

    start_time = time.time()
    graph = create_research_graph()

    initial_state: ResearchState = {
        "topic": topic,
        "pdf_paths": pdf_paths,
        "researcher_output": None,
        "reader_output": None,
        "analyst_output": None,
        "final_report": None,
        "iteration_count": 0,
        "status_message": "Initialized pipeline.",
        "error_message": None
    }

    try:
        final_state = graph.invoke(initial_state)
        duration = time.time() - start_time
        report = final_state.get("final_report")

        # Collect source counts
        res_sources = len(final_state["researcher_output"].sources) if final_state.get("researcher_output") else 0
        read_chunks = len(final_state["reader_output"].chunks) if final_state.get("reader_output") else 0
        total_sources = res_sources + read_chunks

        # Export report
        md_file = export_to_markdown(report)
        pdf_file = export_to_pdf(report)

        # Record telemetry
        tracker.record_run(
            topic=topic,
            duration_seconds=duration,
            success=True,
            sources_count=total_sources,
            agent_statuses={
                "researcher": "completed",
                "reader": "completed",
                "analyst": "completed",
                "writer": "completed"
            }
        )

        print("\n" + "=" * 60)
        print("✅ RESEARCH REPORT GENERATED SUCCESSFULLY")
        print("=" * 60)
        print(f"⏱  Execution Time: {duration:.1f} seconds")
        print(f"🌐 Sources Indexed: {total_sources} (Web: {res_sources}, Documents: {read_chunks})")
        print(f"📝 Markdown Export: {md_file}")
        print(f"📑 PDF Export:      {pdf_file}")
        print("=" * 60 + "\n")

        return final_state

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        tracker.record_run(
            topic=topic,
            duration_seconds=duration,
            success=False,
            sources_count=0,
            agent_statuses={"pipeline": "failed"},
            error_msg=str(e)
        )
        print(f"\n❌ Error during execution: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-Agent Research Assistant")
    parser.add_argument("--topic", type=str, required=True, help="Research topic or question")
    parser.add_argument("--pdf", nargs="*", default=[], help="Paths to PDF documents")
    
    args = parser.parse_args()
    run_pipeline(args.topic, args.pdf)

