from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Any

from backend.agents.framing_extractor import framing_extractor
from backend.agents.fact_extractor     import fact_extractor
from backend.agents.omission_detector  import omission_detector
from backend.agents.bias_scorer        import bias_scorer


class BiasState(TypedDict):
    articles:          List[Dict[str, Any]]   # [{url, title, text}]
    framing_results:   List[Dict[str, Any]]
    fact_results:      List[Dict[str, Any]]
    omission_analysis: str
    bias_scores:       List[Dict[str, Any]]
    bias_narrative:    str
    final_report:      str


def create_bias_workflow():
    graph = StateGraph(BiasState)

    graph.add_node("framing_extractor",  framing_extractor)
    graph.add_node("fact_extractor",     fact_extractor)
    graph.add_node("omission_detector",  omission_detector)
    graph.add_node("bias_scorer",        bias_scorer)

    graph.set_entry_point("framing_extractor")
    graph.add_edge("framing_extractor", "fact_extractor")
    graph.add_edge("fact_extractor",    "omission_detector")
    graph.add_edge("omission_detector", "bias_scorer")
    graph.add_edge("bias_scorer",       END)

    return graph.compile()
