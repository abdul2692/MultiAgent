"""
Exercise 2: Your First Real LangGraph Workflow
Teaches: StateGraph, Nodes, Edges, START, and END.
"""
from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END

# Step 1: Define the Shared State Schema
# Every agent node receives this dictionary and returns fields to update.
class PipelineState(TypedDict):
    topic: str
    search_queries: List[str]
    raw_findings: List[str]
    report: str

# Step 2: Define Agent Nodes
def researcher_node(state: PipelineState) -> dict:
    """Agent 1: Generates search queries and collects simulated sources."""
    print("  -> [Node: Researcher] Gathering data for topic:", state["topic"])
    return {
        "search_queries": [
            f"{state['topic']} fundamentals",
            f"{state['topic']} challenges and trends"
        ],
        "raw_findings": [
            "Source A: Solid-state replaces flammable liquid electrolytes with ceramic/polymer separators.",
            "Source B: Key bottleneck remains high manufacturing cost and dendrite formation under fast charging."
        ]
    }

def writer_node(state: PipelineState) -> dict:
    """Agent 2: Ingests findings from State and produces the structured report."""
    print("  -> [Node: Writer] Assembling report...")
    formatted_sources = "\n".join(f"- {s}" for s in state["raw_findings"])
    final_text = (
        f"# Research Brief: {state['topic']}\n\n"
        f"## Synthesized Evidence\n{formatted_sources}\n\n"
        f"## Status: Verified by LangGraph Multi-Agent Pipeline."
    )
    return {"report": final_text}

# Step 3: Build the LangGraph StateGraph
def build_graph():
    # Initialize the graph with the schema
    workflow = StateGraph(PipelineState)

    # Add Nodes (Name of Node, Function that executes)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("writer", writer_node)

    # Define the Edges (Flow of control)
    # START -> researcher -> writer -> END
    workflow.add_edge(START, "researcher")
    workflow.add_edge("researcher", "writer")
    workflow.add_edge("writer", END)

    # Compile the graph into an executable runnable
    app = workflow.compile()
    return app

if __name__ == "__main__":
    print("=== Compiling and Executing LangGraph Workflow ===")
    app = build_graph()

    # Initial input data to seed the graph
    initial_input: PipelineState = {
        "topic": "Solid-State Battery Adoption in Aerospace",
        "search_queries": [],
        "raw_findings": [],
        "report": ""
    }

    # Execute the workflow
    result = app.invoke(initial_input)

    print("\n=== Workflow Completed Successfully ===")
    print("Final State 'report' output:\n")
    print(result["report"])

