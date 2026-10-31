"""
Exercise 3: Conditional Routing in LangGraph
Teaches: Conditional Edges (Dynamic Decision Making) based on State.
"""
from typing import TypedDict, List, Literal
from langgraph.graph import StateGraph, START, END

class ResearchState(TypedDict):
    topic: str
    search_queries: List[str]
    collected_facts: List[str]
    iteration_count: int
    quality_status: str
    final_output: str

# 1. Researcher Node: Simulates searching and collecting data
def researcher_node(state: ResearchState) -> dict:
    count = state.get("iteration_count", 0) + 1
    print(f"\n[Researcher Node (Attempt #{count})]")
    
    if count == 1:
        # First attempt: sparse data simulate insufficient search results
        print("  -> Findings were too sparse. Collected only 1 fact.")
        return {
            "collected_facts": ["Fact 1: Solid-state batteries have higher theoretical energy density."],
            "iteration_count": count
        }
    else:
        # Second attempt: rich data
        print("  -> Expanded search queries! Collected high-depth facts.")
        return {
            "collected_facts": state["collected_facts"] + [
                "Fact 2: Solid electrolytes eliminate volatile liquid flammability risks.",
                "Fact 3: Manufacturing scale-up is projected for commercial rollout by 2028."
            ],
            "iteration_count": count
        }

# 2. Quality Evaluator (Decision Function for Conditional Edge)
def evaluate_research_quality(state: ResearchState) -> Literal["expand_search", "proceed_to_writer"]:
    """
    This is NOT a node that mutates state.
    It is a ROUTER FUNCTION that inspects state and decides the next node.
    """
    facts_count = len(state.get("collected_facts", []))
    print(f"[Router Function] Evaluating state: {facts_count} facts collected.")
    
    if facts_count < 3 and state.get("iteration_count", 0) < 3:
        print("  -> Quality Gate: INSUFFICIENT. Routing back to 'researcher' for retry.")
        return "expand_search"
    
    print("  -> Quality Gate: PASSED. Routing to 'writer'.")
    return "proceed_to_writer"

# 3. Writer Node
def writer_node(state: ResearchState) -> dict:
    print("\n[Writer Node] Generating synthesized brief...")
    bullet_points = "\n".join(f"- {f}" for f in state["collected_facts"])
    report = (
        f"# Research Brief: {state['topic']}\n"
        f"Attempts needed: {state['iteration_count']}\n\n"
        f"## Verified Findings:\n{bullet_points}"
    )
    return {"final_output": report, "quality_status": "APPROVED"}

# 4. Constructing the Graph with a Conditional Edge (Loop)
def build_conditional_graph():
    graph = StateGraph(ResearchState)

    graph.add_node("researcher", researcher_node)
    graph.add_node("writer", writer_node)

    # Edge from START to researcher
    graph.add_edge(START, "researcher")

    # CONDITIONAL EDGE from researcher:
    # Based on the return value of evaluate_research_quality,
    # the graph routes either back to 'researcher' or forwards to 'writer'.
    graph.add_conditional_edges(
        "researcher",
        evaluate_research_quality,
        {
            "expand_search": "researcher",      # Loop back (Refinement cycle)
            "proceed_to_writer": "writer"       # Proceed forward
        }
    )

    # Edge from writer to END
    graph.add_edge("writer", END)

    return graph.compile()

if __name__ == "__main__":
    print("=== Starting Conditional Multi-Agent Graph ===")
    app = build_conditional_graph()

    initial_state: ResearchState = {
        "topic": "Solid-State Aviation Batteries",
        "search_queries": [],
        "collected_facts": [],
        "iteration_count": 0,
        "quality_status": "PENDING",
        "final_output": ""
    }

    result = app.invoke(initial_state)

    print("\n=== Workflow Completed Successfully ===")
    print(result["final_output"])

