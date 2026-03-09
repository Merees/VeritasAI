from typing import TypedDict, List


class AgentState(TypedDict):
    input_news: str
    claim: str
    evidence: List[str]
    sources: List[str]
    credibility_score: float
    summary: str
    report: str