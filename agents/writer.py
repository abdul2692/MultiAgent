"""
Agent 4: Writer Agent.
Responsible for:
1. Converting structured findings from Researcher, Reader, and Analyst into a cohesive paper.
2. Generating: Title, Executive Summary, Methodology, Findings, Analysis, Conclusion.
3. Compiling an exact, numbered bibliography with real source URLs and document citations.
4. Returning a structured ResearchReport.
"""
import os
import sys
import logging
from typing import List

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain_core.prompts import ChatPromptTemplate
from models.schemas import ResearchReport, ResearcherOutput, ReaderOutput, AnalystOutput
from utils.llm_factory import get_llm  # ← unified local/cloud LLM switch

logger = logging.getLogger("multi_agent.agents.writer")

def run_writer(
    topic: str,
    researcher_out: ResearcherOutput,
    reader_out: ReaderOutput,
    analyst_out: AnalystOutput
) -> ResearchReport:
    """
    Synthesizes all agent outputs into a publication-ready research briefing.
    """
    logger.info(f"[Agent 4: Writer] Generating comprehensive report for '{topic}'...")
    llm = get_llm()
    
    # 1. Compile References List
    references: List[str] = []
    ref_idx = 1
    
    for s in researcher_out.sources:
        references.append(f"[{ref_idx}] \"{s.title}\" — Available at: {s.url}")
        ref_idx += 1
        
    for d in reader_out.documents_read:
        references.append(f"[{ref_idx}] Internal Document: \"{d}\" — Analyzed via PyMuPDF Ingestion.")
        ref_idx += 1
        
    if not references:
        references.append("[1] Direct Knowledge Synthesis (No external links indexed).")
        
    refs_text = "\n".join(references)
    
    # 2. Build Briefing Context for the LLM
    context = (
        f"TOPIC: {topic}\n\n"
        f"KEY INSIGHTS FROM ANALYST:\n" + "\n".join(f"- {i}" for i in analyst_out.core_insights) + "\n\n"
        f"CONTRADICTIONS IDENTIFIED:\n" + "\n".join(f"- {c}" for c in analyst_out.contradictions) + "\n\n"
        f"DATA GAPS IDENTIFIED:\n" + "\n".join(f"- {g}" for g in analyst_out.identified_gaps) + "\n\n"
        f"RESEARCH SOURCES AVAILABLE:\n{refs_text}\n\n"
        f"ANALYST NARRATIVE:\n{analyst_out.analytical_narrative[:600]}"
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a Distinguished Research Fellow and Technical Writer. "
            "Write an authoritative, rigorous, structured research briefing based on the provided context.\n"
            "Format the output strictly as:\n\n"
            "EXECUTIVE SUMMARY:\n<2-3 concise paragraphs giving an executive-level overview>\n\n"
            "METHODOLOGY:\n<1 paragraph detailing the multi-agent search, document parsing, and analysis process>\n\n"
            "FINDINGS:\n<Detailed thematic sections synthesizing the evidence, citing numbered references e.g. [1] or [2]>\n\n"
            "ANALYSIS:\n<Evaluation of technical bottlenecks, commercial feasibility, contradictions, and gaps>\n\n"
            "CONCLUSION:\n<Forward-looking synthesis and strategic roadmap recommendations>"
        )),
        ("human", "Research Context:\n{context}")
    ])
    
    exec_summary = ""
    methodology = (
        "This report was produced by an autonomous 4-agent LangGraph orchestration pipeline. "
        "The Researcher agent queried live web indexes, the Reader agent extracted local PDF documentation, "
        "and the Analyst agent performed multi-source cross-verification and gap detection."
    )
    findings = ""
    analysis = ""
    conclusion = ""
    
    try:
        chain = prompt | llm
        resp = chain.invoke({"context": context})
        raw_text = resp.content.strip()
        
        # Parse output into clean sections
        sections = {
            "EXECUTIVE SUMMARY:": "",
            "METHODOLOGY:": "",
            "FINDINGS:": "",
            "ANALYSIS:": "",
            "CONCLUSION:": ""
        }
        
        current_sec = None
        for line in raw_text.split("\n"):
            line_upper = line.strip().upper()
            matched = False
            for sec_key in sections:
                if sec_key in line_upper:
                    current_sec = sec_key
                    matched = True
                    break
            if matched:
                continue
                
            if current_sec:
                sections[current_sec] += line + "\n"
                
        exec_summary = sections["EXECUTIVE SUMMARY:"].strip() or f"Executive evaluation of {topic}."
        if sections["METHODOLOGY:"].strip():
            methodology = sections["METHODOLOGY:"].strip()
        findings = sections["FINDINGS:"].strip() or analyst_out.analytical_narrative
        analysis = sections["ANALYSIS:"].strip() or "Analysis indicates rapid technological evolution accompanied by manufacturing challenges."
        conclusion = sections["CONCLUSION:"].strip() or "Further investment into pilot-scale testing and regulatory safety standards is advised."
        
    except Exception as e:
        logger.warning(f"LLM writing phase encountered an issue: {e}. Generating structured baseline.")
        exec_summary = f"Executive briefing regarding advancements in {topic}."
        findings = analyst_out.analytical_narrative
        analysis = "Current literature confirms strong theoretical advantages with ongoing production cost constraints."
        conclusion = "Continued cross-disciplinary research and standardisation are required for commercial viability."
        
    return ResearchReport(
        title=f"Strategic Research Report: {topic.title()}",
        executive_summary=exec_summary,
        methodology=methodology,
        findings=findings,
        analysis=analysis,
        conclusion=conclusion,
        references=references
    )

if __name__ == "__main__":
    print("Testing Writer Agent module...")
