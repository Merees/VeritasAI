from backend.models.ollama_client import get_llm

llm = get_llm()


def claim_extractor(state):

    news = state["input_news"]

    prompt = f"""
You are a fact-checking assistant.

Extract the main factual claim from the news headline or article below.

Rules:
- Return ONLY the claim.
- Do NOT include explanations.
- Do NOT include phrases like "The main claim is".
- Output must be a single sentence.

News:
{news}
"""

    response = llm.invoke(prompt)

    claim = str(response.content).strip()

    # Clean common unwanted prefixes
    unwanted_prefixes = [
        "The main factual claim is:",
        "Main claim:",
        "Claim:",
        "The claim is:"
    ]

    for prefix in unwanted_prefixes:
        if claim.startswith(prefix):
            claim = claim.replace(prefix, "").strip()

    return {
        **state,
        "claim": claim
    }