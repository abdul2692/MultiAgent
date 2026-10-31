"""
Pydantic Schemas for Multi-Agent Research Assistant.
Defines structured data contracts between agents.
"""
from typing import List, Optional
from pydantic import BaseModel, Field

class WebSearchResult(BaseModel):
    """Represents a single web search hit."""
    title: str = Field(description="Title of the web page")
    url: str = Field(description="Direct URL to the source")
    snippet: str = Field(description="Key excerpt or summary from the search result")

class ResearcherOutput(BaseModel):
    """Structured output produced by Agent 1: Researcher."""
    topic: str = Field(description="The primary research query or topic")
    queries_used: List[str] = Field(description="Search queries generated to explore the topic")
    sources: List[WebSearchResult] = Field(default_factory=list, description="Collected web sources")
    summary: str = Field(description="Initial factual synthesis from web search")

class DocumentChunk(BaseModel):
    """Represents an extracted passage from an uploaded PDF document."""
    file_name: str = Field(description="Name of the PDF file")
    page_number: int = Field(description="1-based page number where the text appears")
    text: str = Field(description="Extracted text chunk")

class ReaderOutput(BaseModel):
    """Structured output produced by Agent 2: Reader."""
    documents_read: List[str] = Field(default_factory=list, description="List of filenames analyzed")
    chunks: List[DocumentChunk] = Field(default_factory=list, description="Relevant text passages with citations")
    document_summary: str = Field(description="Summary of facts extracted from local documents")
    key_facts: List[str] = Field(default_factory=list, description="Bullet points of verified facts from documents")

class AnalystOutput(BaseModel):
    """Structured output produced by Agent 3: Analyst."""
    core_insights: List[str] = Field(description="Key overarching insights synthesized across all sources")
    contradictions: List[str] = Field(default_factory=list, description="Contradicting data points found across sources")
    identified_gaps: List[str] = Field(default_factory=list, description="Questions or areas lacking sufficient evidence")
    source_quality_score: float = Field(ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0 on data reliability")
    analytical_narrative: str = Field(description="Comprehensive technical analysis connecting web and doc evidence")

class ResearchReport(BaseModel):
    """Structured output produced by Agent 4: Writer."""
    title: str = Field(description="Formal title of the research report")
    executive_summary: str = Field(description="High-level executive briefing")
    methodology: str = Field(description="Overview of research methods and agents applied")
    findings: str = Field(description="Detailed synthesized findings")
    analysis: str = Field(description="Critical evaluation, challenges, and trends")
    conclusion: str = Field(description="Forward-looking conclusion and recommendations")
    references: List[str] = Field(default_factory=list, description="Numbered bibliography and URL references")

