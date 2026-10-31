"""
Exercise 1: The Blackboard (Shared State) Pattern in Pure Python
Demonstrates how multiple specialized agents collaborate through a single state dictionary.
"""
from typing import TypedDict, List

# 1. Define the Shared State Schema
class ResearchState(TypedDict):
    topic: str
    search_queries: List[str]
    raw_web_data: List[str]
    analysis_notes: str
    final_summary: str

# 2. Agent 1: Researcher Node
def researcher_agent(state: ResearchState) -> dict:
    print("\n[Agent 1: Researcher] Analyzing topic...")
    topic = state["topic"]
    # Formulate targeted queries based on the topic
    queries = [f"{topic} overview", f"{topic} latest breakthroughs 2025"]
    
    # Simulate web search results
    search_results = [
        f"Result 1 for {queries[0]}: Solid-state batteries use solid electrolytes instead of liquid ones.",
        f"Result 2 for {queries[1]}: Recent lab tests show 400 Wh/kg energy density achieved."
    ]
    
    # Return ONLY the keys this agent is responsible for updating
    return {
        "search_queries": queries,
        "raw_web_data": search_results
    }

# 3. Agent 2: Analyst Node
def analyst_agent(state: ResearchState) -> dict:
    print("\n[Agent 2: Analyst] Synthesizing raw data...")
    raw_data = state["raw_web_data"]
    
    # Analyze and spot key trends
    synthesis = "Key Finding: Transition from liquid to solid electrolyte enables higher energy density (400 Wh/kg)."
    
    return {
        "analysis_notes": synthesis
    }

# 4. Agent 3: Writer Node
def writer_agent(state: ResearchState) -> dict:
    print("\n[Agent 3: Writer] Formatting final report...")
    topic = state["topic"]
    analysis = state["analysis_notes"]
    
    report = (
        f"# Executive Briefing: {topic.title()}\n"
        f"## Summary of Findings\n{analysis}\n"
        f"## Sources Consulted\n" + "\n".join(f"- {q}" for q in state["search_queries"])
    )
    
    return {
        "final_summary": report
    }

# 5. Workflow Execution (Sequential Orchestration)
if __name__ == "__main__":
    # Initial State
    state: ResearchState = {
        "topic": "Solid-state batteries in aviation",
        "search_queries": [],
        "raw_web_data": [],
        "analysis_notes": "",
        "final_summary": ""
    }

    print("--- Starting Pipeline with Initial State ---")
    print(f"Topic: {state['topic']}")

    # Step 1: Researcher runs and updates state
    state.update(researcher_agent(state))

    # Step 2: Analyst runs and updates state
    state.update(analyst_agent(state))

    # Step 3: Writer runs and updates state
    state.update(writer_agent(state))

    print("\n================ FINAL REPORT ================")
    print(state["final_summary"])

