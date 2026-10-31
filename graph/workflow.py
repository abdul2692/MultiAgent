"""
Multi-Agent Orchestration Workflow with LangGraph.
Implements:
1. Shared state propagation.
2. Nodes for Researcher, Reader, Analyst, Writer.
3. Conditional edge for research quality gate (retry loop).
4. Sequential pipeline execution.
5. Error handling and workflow compilation.
"""
import os
import sys
import logging
from typing import Literal
from langgraph.graph import StateGraph, START, END

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from graph.state import ResearchState
from agents.researcher import run_researcher
from agents.reader import run_reader
from agents.analyst import run_analyst
from agents.writer import run_writer
from models.schemas import ResearcherOutput, ReaderOutput, AnalystOutput, ResearchReport

logger = logging.getLogger("multi_agent.graph.workflow")

# -------------------------------------------------------------
# 1. Agent Node Functions
# -------------------------------------------------------------

def researcher_node(state: ResearchState) -> dict:
    """Agent 1: Mines live web sources for the topic."""
    current_iter = state.get("iteration_count", 0) + 1
    topic = state["topic"]
    logger.info(f"--- [Node: Researcher] Attempt #{current_iter} for '{topic}' ---")
    
    try:
        researcher_out = run_researcher(topic, max_results_per_query=3)
        return {
            "researcher_output": researcher_out,
            "iteration_count": current_iter,
            "status_message": f"Researcher collected {len(researcher_out.sources)} web sources."
        }
    except Exception as e:
        logger.error(f"Researcher node error: {e}", exc_info=True)
        fallback = ResearcherOutput(
            topic=topic,
            queries_used=[topic],
            sources=[],
            summary=f"Automated search encountered an error: {str(e)}"
        )
        return {
            "researcher_output": fallback,
            "iteration_count": current_iter,
            "status_message": "Researcher encountered an error; proceeding with fallback data."
        }

def reader_node(state: ResearchState) -> dict:
    """Agent 2: Parses and extracts text chunks from PDF documents."""
    pdf_paths = state.get("pdf_paths", [])
    logger.info(f"--- [Node: Reader] Ingesting {len(pdf_paths)} documents ---")
    
    try:
        reader_out = run_reader(pdf_paths)
        return {
            "reader_output": reader_out,
            "status_message": f"Reader analyzed {len(reader_out.documents_read)} documents ({len(reader_out.chunks)} passages)."
        }
    except Exception as e:
        logger.error(f"Reader node error: {e}", exc_info=True)
        fallback = ReaderOutput(
            documents_read=[],
            chunks=[],
            document_summary="PDF reader encountered an issue.",
            key_facts=[]
        )
        return {
            "reader_output": fallback,
            "status_message": "Reader error encountered; proceeding without document data."
        }

def analyst_node(state: ResearchState) -> dict:
    """Agent 3: Evaluates patterns, contradictions, and gaps."""
    logger.info("--- [Node: Analyst] Synthesizing web & document findings ---")
    topic = state["topic"]
    res_out = state["researcher_output"]
    read_out = state["reader_output"]
    
    try:
        analyst_out = run_analyst(topic, res_out, read_out)
        return {
            "analyst_output": analyst_out,
            "status_message": f"Analyst identified {len(analyst_out.core_insights)} core insights (Quality: {analyst_out.source_quality_score * 100:.0f}%)."
        }
    except Exception as e:
        logger.error(f"Analyst node error: {e}", exc_info=True)
        fallback = AnalystOutput(
            core_insights=[f"Baseline evaluation of {topic}."],
            contradictions=[],
            identified_gaps=["Additional empirical research required."],
            source_quality_score=0.4,
            analytical_narrative="Analysis generated from baseline records."
        )
        return {
            "analyst_output": fallback,
            "status_message": "Analyst error encountered; using baseline analysis."
        }

def writer_node(state: ResearchState) -> dict:
    """Agent 4: Converts analytical findings into publication report."""
    logger.info("--- [Node: Writer] Assembling formal research report ---")
    topic = state["topic"]
    res_out = state["researcher_output"]
    read_out = state["reader_output"]
    analyst_out = state["analyst_output"]
    
    try:
        report = run_writer(topic, res_out, read_out, analyst_out)
        return {
            "final_report": report,
            "status_message": "Writer completed formal research report with citations."
        }
    except Exception as e:
        logger.error(f"Writer node error: {e}", exc_info=True)
        fallback_report = ResearchReport(
            title=f"Research Brief: {topic.title()}",
            executive_summary="Executive briefing on research topic.",
            methodology="Autonomous 4-agent LangGraph workflow.",
            findings="Key findings compiled across sources.",
            analysis="Strategic evaluation of available data points.",
            conclusion="Continued research and monitoring recommended.",
            references=["[1] Autonomous Research Assistant Knowledge Base."]
        )
        return {
            "final_report": fallback_report,
            "status_message": "Writer generated fallback report format."
        }

# -------------------------------------------------------------
# 2. Conditional Routing (Quality Gate)
# -------------------------------------------------------------

def evaluate_research_gate(state: ResearchState) -> Literal["retry_research", "proceed_to_reader"]:
    """
    Quality gate: Checks if the researcher found at least 1 verified source.
    If 0 sources found and under max retry threshold (2), routes back to researcher.
    """
    res_out = state.get("researcher_output")
    sources_count = len(res_out.sources) if res_out else 0
    iteration = state.get("iteration_count", 0)
    
    logger.info(f"[Quality Gate] Sources found: {sources_count}, Iteration: {iteration}")
    
    if sources_count == 0 and iteration < 2:
        logger.warning("[Quality Gate] Zero sources found. Triggering research retry.")
        return "retry_research"
        
    return "proceed_to_reader"

# -------------------------------------------------------------
# 3. LangGraph Workflow Construction
# -------------------------------------------------------------

def create_research_graph():
    """
    Builds and compiles the complete LangGraph StateGraph:
    START -> researcher -> (conditional gate) -> reader -> analyst -> writer -> END
    """
    workflow = StateGraph(ResearchState)
    
    # Add Nodes
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("reader", reader_node)
    workflow.add_node("analyst", analyst_node)
    workflow.add_node("writer", writer_node)
    
    # Define Flow Edges
    workflow.add_edge(START, "researcher")
    
    # Conditional Edge: Quality Gate from Researcher
    workflow.add_conditional_edges(
        "researcher",
        evaluate_research_gate,
        {
            "retry_research": "researcher",
            "proceed_to_reader": "reader"
        }
    )
    
    workflow.add_edge("reader", "analyst")
    workflow.add_edge("analyst", "writer")
    workflow.add_edge("writer", END)
    
    # Compile the graph
    app = workflow.compile()
    return app

if __name__ == "__main__":
    print("=== Testing Full LangGraph Multi-Agent Orchestration ===")
    graph = create_research_graph()
    
    initial_state: ResearchState = {
        "topic": "Quantum Computing in Drug Discovery",
        "pdf_paths": [],
        "researcher_output": None,
        "reader_output": None,
        "analyst_output": None,
        "final_report": None,
        "iteration_count": 0,
        "status_message": "Pipeline initialized.",
        "error_message": None
    }
    
    # Execute the graph
    final_output = graph.invoke(initial_state)
    report = final_output.get("final_report")
    
    print("\n================ FINAL GENERATED REPORT ================")
    print(f"Title: {report.title}\n")
    print(f"Executive Summary:\n{report.executive_summary}\n")
    print(f"Methodology:\n{report.methodology}\n")
    print(f"Findings:\n{report.findings}\n")
    print(f"Analysis:\n{report.analysis}\n")
    print(f"Conclusion:\n{report.conclusion}\n")
    print("References:")
    for ref in report.references:
        print(f"  {ref}")

