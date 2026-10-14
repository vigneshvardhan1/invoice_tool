"""Day 1: minimal LangGraph pipeline. No LLM yet.

Run: python graph.py
Expected: {'filename': 'sample.pdf', 'status': 'validated: sample.pdf'}
"""
from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class InvoiceState(TypedDict):
    filename: str
    status: str


def load_input(state: InvoiceState) -> dict:
    return {"status": f"loaded: {state['filename']}"}


def validate_stub(state: InvoiceState) -> dict:
    return {"status": f"validated: {state['filename']}"}


def build_graph():
    builder = StateGraph(InvoiceState)
    builder.add_node("load", load_input)
    builder.add_node("validate", validate_stub)
    builder.add_edge(START, "load")
    builder.add_edge("load", "validate")
    builder.add_edge("validate", END)
    return builder.compile()


if __name__ == "__main__":
    app = build_graph()
    result = app.invoke({"filename": "sample.pdf", "status": "new"})
    print(result)
