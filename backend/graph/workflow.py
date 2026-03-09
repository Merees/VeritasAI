from langgraph.graph import StateGraph, END

from backend.graph.state import AgentState
from backend.agents.claim_extractor import claim_extractor
from backend.agents.evidence_retriever import evidence_retriever
from backend.agents.source_analyzer import source_analyzer
from backend.agents.fact_verifier import fact_verifier
from backend.agents.report_generator import report_generator


def create_workflow():

    workflow = StateGraph(AgentState)

    workflow.add_node("claim_extractor", claim_extractor)
    workflow.add_node("evidence_retriever", evidence_retriever)
    workflow.add_node("source_analyzer", source_analyzer)
    workflow.add_node("fact_verifier", fact_verifier)
    workflow.add_node("report_generator", report_generator)

    workflow.set_entry_point("claim_extractor")

    workflow.add_edge("claim_extractor", "evidence_retriever")
    workflow.add_edge("evidence_retriever", "source_analyzer")
    workflow.add_edge("source_analyzer", "fact_verifier")
    workflow.add_edge("fact_verifier", "report_generator")
    workflow.add_edge("report_generator", END)

    return workflow.compile()