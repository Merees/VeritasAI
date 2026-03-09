from backend.models.ollama_client import get_llm

llm = get_llm()


def omission_detector(state):
    """
    Agent 3 — Compare fact lists across articles and detect what each omits.
    """
    articles      = state["articles"]
    fact_results  = state["fact_results"]
    framing_results = state["framing_results"]

    # Build a combined facts summary for comparison
    facts_summary = ""
    for i, fr in enumerate(fact_results):
        facts_summary += f"\n\nARTICLE {i+1} — {fr['title']} ({fr['url']})\n{fr['facts']}"

    framing_summary = ""
    for i, fr in enumerate(framing_results):
        framing_summary += f"\n\nARTICLE {i+1} — {fr['title']}\n{fr['framing']}"

    prompt = f"""
Compare these news articles covering the same story. Be brief — 2-3 sentences per section. Do NOT use bullet points, asterisks, or markdown. Write in plain sentences only.

Facts per article:
{facts_summary}

Format exactly as:
Shared Facts: <2-3 sentences>
Unique To Each Article: <1-2 sentences per article, clearly labelled by source name>
Contradictions: <1-2 sentences or "None detected">
Context Gaps: <1-2 sentences>
Narrative Differences: <2-3 sentences>
"""
    response = llm.invoke(prompt)

    return {
        **state,
        "omission_analysis": str(response.content).strip()
    }