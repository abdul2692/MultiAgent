"""
Agent 1: Researcher Agent.
Responsible for:
1. Decomposing the research topic into targeted search queries.
2. Executing free web searches.
3. Mining URLs, titles, and factual snippets.
4. Returning structured ResearcherOutput.
"""
import os
import sys
import logging
from typing import List

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain_core.prompts import ChatPromptTemplate
from models.schemas import ResearcherOutput, WebSearchResult
from tools.web_search import search_web
from utils.llm_factory import get_llm  # ← unified local/cloud LLM switch

logger = logging.getLogger("multi_agent.agents.researcher")

def generate_search_queries(topic: str, llm=None) -> List[str]:
    """
    Uses LLM to formulate 2 distinct, highly targeted search queries.
    """
    if llm is None:
        llm = get_llm()
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a Senior Academic Researcher. Your job is to generate 2 distinct, highly effective "
            "search engine queries for the user's research topic. "
            "Output ONLY the queries, one per line. Do not include numbers, bullets, or extra text."
        )),
        ("human", "Research Topic: {topic}")
    ])
    
    chain = prompt | llm
    try:
        response = chain.invoke({"topic": topic})
        lines = [line.strip().lstrip("1234567890.-* ") for line in response.content.strip().split("\n") if line.strip()]
        queries = [q for q in lines if len(q) > 4][:2]
        if not queries:
            queries = [f"{topic} overview breakthroughs", f"{topic} current challenges 2025"]
        return queries
    except Exception as e:
        logger.warning(f"LLM query generation failed ({e}), using rule-based search queries.")
        return [f"{topic} technology overview", f"{topic} market applications"]

def run_researcher(topic: str, max_results_per_query: int = 3) -> ResearcherOutput:
    """
    Orchestrates the Researcher Agent execution:
    1. Formulates search queries.
    2. Searches the web.
    3. Synthesizes findings using local LLM.
    """
    logger.info(f"[Agent 1: Researcher] Starting research for topic: '{topic}'")
    llm = get_llm()
    
    # 1. Generate search queries
    queries = generate_search_queries(topic, llm)
    logger.info(f"Generated queries: {queries}")
    
    # 2. Execute Web Searches
    all_sources: List[WebSearchResult] = []
    seen_urls = set()
    
    for q in queries:
        hits = search_web(q, max_results=max_results_per_query)
        for h in hits:
            if h.url not in seen_urls:
                seen_urls.add(h.url)
                all_sources.append(h)
                
    # 3. Synthesize Initial Findings using LLM
    context_text = "\n\n".join([f"Source: {s.title}\nURL: {s.url}\nExcerpt: {s.snippet}" for s in all_sources])
    
    summary_prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a Research Synthesizer. Review the web excerpts provided and summarize the top facts "
            "discovered about the topic. Maintain strict objectivity and mention relevant source details."
        )),
        ("human", "Research Topic: {topic}\n\nWeb Excerpts:\n{context}\n\nSummary of Web Findings:")
    ])
    
    summary = ""
    try:
        summary_chain = summary_prompt | llm
        summary_resp = summary_chain.invoke({"topic": topic, "context": context_text})
        summary = summary_resp.content.strip()
    except Exception as e:
        logger.warning(f"LLM web summary failed: {e}. Generating baseline summary.")
        summary = f"Gathered {len(all_sources)} web sources on {topic}."
        
    return ResearcherOutput(
        topic=topic,
        queries_used=queries,
        sources=all_sources,
        summary=summary
    )

if __name__ == "__main__":
    print("Testing Researcher Agent independently...")
    res = run_researcher("Solid-State Batteries in Aerospace", max_results_per_query=2)
    print(f"\nTopic: {res.topic}")
    print(f"Queries Used: {res.queries_used}")
    print(f"Total Sources Found: {len(res.sources)}")
    print(f"\nResearcher Summary:\n{res.summary}")
