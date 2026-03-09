from backend.models.ollama_client import get_llm
import re

llm = get_llm()


def fact_verifier(state):

    claim    = state["claim"]
    evidence = state["evidence"]

    prompt = f"""
You are a senior fact-checking journalist with expertise in verifying news claims.

Claim to verify:
{claim}

Evidence gathered from news articles:
{evidence}

Your job is to produce a thorough, professional fact-check report. Follow these instructions carefully:

1. CREDIBILITY SCORE (0-100):
   - 0-30:  False or highly misleading — evidence contradicts the claim
   - 31-60: Uncertain or mixed — evidence is inconclusive or partially supports the claim
   - 61-100: Credible — evidence strongly supports the claim

2. VERDICT: State clearly whether the claim is TRUE, FALSE, MISLEADING, or UNVERIFIED.

3. DETAILED ANALYSIS (this is the most important section):
   - Write at least 4-6 full paragraphs
   - Paragraph 1: Restate and contextualise the claim
   - Paragraph 2: Summarise what the evidence says
   - Paragraph 3: Point out specific facts from the evidence that support or contradict the claim
   - Paragraph 4: Discuss any nuance, missing context, or ways the claim could be misleading even if partially true
   - Paragraph 5: Assess the quality and reliability of the sources consulted
   - Paragraph 6: Final conclusion — what should a reader understand about this claim

4. Be specific. Reference actual details from the evidence. Do not be vague.
5. Write in clear, professional English. No bullet points — full paragraphs only.

Format your response exactly like this:

Credibility Score: <number>

Verdict: <TRUE / FALSE / MISLEADING / UNVERIFIED>

Analysis:
<your detailed multi-paragraph analysis here>
"""

    response = llm.invoke(prompt)

    result_text = str(response.content).strip()

    # Extract numeric score — find the one right after "Credibility Score:"
    score_match = re.search(r'Credibility Score:\s*(\d+)', result_text)
    if not score_match:
        score_match = re.search(r'\d+', result_text)

    credibility_score = int(score_match.group(1) if score_match.lastindex else score_match.group()) if score_match else 0

    return {
        **state,
        "credibility_score": credibility_score,
        "report":            result_text
    }








