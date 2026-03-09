from backend.models.ollama_client import get_llm
import re
import json

llm = get_llm()


def bias_scorer(state):
    """
    Agent 4 — Orchestrator. Synthesises all previous agent outputs into final scores and report.
    """
    articles          = state["articles"]
    framing_results   = state["framing_results"]
    fact_results      = state["fact_results"]
    omission_analysis = state["omission_analysis"]

    # Build full context for orchestrator
    full_context = ""
    for i in range(len(articles)):
        full_context += f"""
ARTICLE {i+1}: {articles[i]['title']}
URL: {articles[i]['url']}

FRAMING ANALYSIS:
{framing_results[i]['framing']}

FACTS EXTRACTED:
{fact_results[i]['facts']}
---
"""

    prompt = f"""
You are a media bias analyst. Produce a concise bias report for {len(articles)} articles covering the same story. Keep each section brief. Do NOT use bullet points, asterisks, dashes, or markdown formatting. Write everything in plain sentences only.

ARTICLE ANALYSES:
{full_context}

OMISSION ANALYSIS:
{omission_analysis}

Write the following sections — 2-3 sentences maximum each:

STORY SUMMARY:
<2 sentences on what the story is about>

OVERALL COMPARISON:
<2-3 sentences comparing how outlets covered this differently>

READER ADVISORY:
<1-2 sentences on what readers should keep in mind>

Also output scores as JSON inside <scores> tags:
<scores>
[
  {{
    "article_index": 0,
    "title": "article title",
    "url": "url",
    "political_lean": "Centre-Left",
    "emotional_intensity": 35,
    "completeness": 72,
    "bias_score": 28
  }}
]
</scores>

Political lean options: Far-Left, Left, Centre-Left, Centre, Centre-Right, Right, Far-Right
All scores: 0-100 integers.
"""

    response = llm.invoke(prompt)
    content  = str(response.content).strip()

    # Extract JSON scores
    scores = []
    scores_match = re.search(r'<scores>(.*?)</scores>', content, re.DOTALL)
    if scores_match:
        try:
            scores = json.loads(scores_match.group(1).strip())
        except Exception:
            scores = []

    # Strip scores block from narrative
    narrative = re.sub(r'<scores>.*?</scores>', '', content, flags=re.DOTALL).strip()

    return {
        **state,
        "bias_scores":   scores,
        "bias_narrative": narrative,
        "final_report":  content
    }