
from backend.models.ollama_client import get_llm

llm = get_llm()


def source_analyzer(state):

    sources = state["sources"]

    prompt = f"""
Evaluate the reliability of the following news sources.

Sources:
{sources}

Classify them as High, Medium, or Low credibility and explain briefly.
"""

    response = llm.invoke(prompt)

    return {
        **state,
        "source_analysis": response.content
    }