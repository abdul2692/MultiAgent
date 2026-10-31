"""
LangGraph Shared State Schema.
Represents the blackboard state passed between all four agents.
"""
from typing import TypedDict, List, Optional
from models.schemas import (
    ResearcherOutput,
    ReaderOutput,
    AnalystOutput,
    ResearchReport
)

class ResearchState(TypedDict):
    """
    The shared state dictionary for our Multi-Agent Research Assistant.
    Each agent reads from and updates designated fields.
    """
    # Inputs
    topic: str
    pdf_paths: List[str]
    
    # Agent Outputs
    researcher_output: Optional[ResearcherOutput]
    reader_output: Optional[ReaderOutput]
    analyst_output: Optional[AnalystOutput]
    final_report: Optional[ResearchReport]
    
    # Control Flow & Reliability
    iteration_count: int
    status_message: str
    error_message: Optional[str]

