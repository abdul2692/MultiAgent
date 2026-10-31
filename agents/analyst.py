"""
Agent 3: Analyst Agent.
Responsible for:
1. Cross-referencing web search findings and document findings.
2. Identifying recurring trends, patterns, and correlations.
3. Detecting contradictions and conflicting data.
4. Spotting research gaps and calculating source quality confidence.
"""
import os
import sys
import logging
from typing import List

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain_core.prompts import ChatPromptTemplate
from models.schemas import AnalystOutput, ResearcherOutput, ReaderOutput
from utils.llm_factory import get_llm  # ← unified local/cloud LLM switch

logger = logging.getLogger("multi_agent.agents.analyst")

def run_analyst(topic: str, researcher_out: ResearcherOutput, reader_out: ReaderOutput) -> AnalystOutput:
    """
    Executes cross-source synthesis and critical analysis.
    """
    logger.info(f"[Agent 3: Analyst] Analyzing evidence for topic: '{topic}'")
    llm = get_llm()
    
    # 1. Prepare aggregated evidence text
    web_evidence = f"WEB SUMMARY:\n{researcher_out.summary}\n\nSOURCES CONSULTED:\n" + "\n".join(
        [f"- {s.title} ({s.url}): {s.snippet}" for s in researcher_out.sources[:4]]
    )
    
    doc_evidence = f"DOCUMENT SUMMARY:\n{reader_out.document_summary}\n\nDOCUMENT FACTS:\n" + "\n".join(
        [f"- {f}" for f in reader_out.key_facts[:4]]
    )
    
    combined_evidence = f"{web_evidence}\n\n{doc_evidence}"
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a Senior Strategic Research Analyst. Your job is to critically evaluate the evidence provided.\n"
            "Produce an objective synthesis covering:\n"
            "1. CORE INSIGHTS: Top 3 major overarching breakthroughs or takeaways.\n"
            "2. CONTRADICTIONS: Any conflicting statements, discrepancies, or disputed estimates.\n"
            "3. GAPS: Crucial aspects missing from the evidence or needing further study.\n"
            "4. ANALYSIS NARRATIVE: A cohesive analytical discussion connecting all evidence.\n\n"
            "Format your reply clearly with those exact headers."
        )),
        ("human", "Research Topic: {topic}\n\nCollected Evidence:\n{evidence}")
    ])
    
    core_insights: List[str] = []
    contradictions: List[str] = []
    identified_gaps: List[str] = []
    analytical_narrative = ""
    
    try:
        chain = prompt | llm
        resp = chain.invoke({"topic": topic, "evidence": combined_evidence})
        content = resp.content.strip()
        
        # Parse sections
        analytical_narrative = content
        
        lines = content.split("\n")
        current_section = None
        for line in lines:
            line_clean = line.strip()
            if "CORE INSIGHTS:" in line_clean.upper():
                current_section = "insights"
                continue
            elif "CONTRADICTIONS:" in line_clean.upper():
                current_section = "contradictions"
                continue
            elif "GAPS:" in line_clean.upper():
                current_section = "gaps"
                continue
            elif "ANALYSIS NARRATIVE:" in line_clean.upper():
                current_section = "narrative"
                continue
                
            if current_section == "insights" and line_clean.startswith(("-", "*", "1", "2", "3")):
                core_insights.append(line_clean.lstrip("1234567890.-* "))
            elif current_section == "contradictions" and line_clean.startswith(("-", "*", "1", "2", "3")):
                contradictions.append(line_clean.lstrip("1234567890.-* "))
            elif current_section == "gaps" and line_clean.startswith(("-", "*", "1", "2", "3")):
                identified_gaps.append(line_clean.lstrip("1234567890.-* "))
                
    except Exception as e:
        logger.warning(f"LLM analysis failed: {e}. Generating baseline analysis.")
        analytical_narrative = f"Aggregated analysis based on {len(researcher_out.sources)} web sources and {len(reader_out.documents_read)} documents."
        
    if not core_insights:
        core_insights = [f"Synthesized evidence from web search regarding {topic}."]
    if not identified_gaps:
        identified_gaps = ["Further empirical testing and long-term deployment metrics are recommended."]
        
    # Calculate source quality confidence score based on actual evidence volume
    web_weight = min(len(researcher_out.sources) * 0.15, 0.6)
    doc_weight = min(len(reader_out.chunks) * 0.1, 0.4)
    quality_score = round(min(web_weight + doc_weight, 1.0), 2)
    if quality_score < 0.2:
        quality_score = 0.5  # Baseline
        
    return AnalystOutput(
        core_insights=core_insights[:4],
        contradictions=contradictions[:3],
        identified_gaps=identified_gaps[:3],
        source_quality_score=quality_score,
        analytical_narrative=analytical_narrative
    )

if __name__ == "__main__":
    print("Testing Analyst Agent independently...")
    dummy_researcher = ResearcherOutput(
        topic="Solid-State Aviation",
        queries_used=["solid-state batteries aerospace"],
        sources=[],
        summary="Solid state batteries promise higher energy density (400 Wh/kg)."
    )
    dummy_reader = ReaderOutput(
        documents_read=[],
        chunks=[],
        document_summary="No documents provided.",
        key_facts=[]
    )
    out = run_analyst("Solid-State Aviation", dummy_researcher, dummy_reader)
    print("Quality Score:", out.source_quality_score)
    print("Insights:", out.core_insights)
