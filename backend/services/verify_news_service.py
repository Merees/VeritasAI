from backend.graph.workflow import create_workflow

workflow = create_workflow()


def verify_news(news_text):

    state = {
        "input_news": news_text,
        "claim": "",
        "evidence": [],
        "sources": [],
        "credibility_score": 0,
        "summary": "",
        "report": ""
    }

    result = workflow.invoke(state)

    return {
        "claim": result["claim"],
        "summary": result["summary"],
        "credibility_score": result["credibility_score"],
        "sources": result["sources"],
        "analysis": result["report"]
    }