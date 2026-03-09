def report_generator(state):

    claim = state["claim"]
    evidence = state["evidence"]
    summary = state.get("summary", "")
    report = state["report"]

    final_report = f"""
NEWS VERIFICATION REPORT

Claim:
{claim}

News Summary:
{summary}

Evidence:
{evidence}

Analysis:
{report}
"""

    return {
        **state,
        "report": final_report
    }