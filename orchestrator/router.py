from agents import summarizer_agent, capture_agent, planner_agent

def route_task(text: str) -> str:
    text_lower = text.lower()

    if "http" in text_lower:
        return summarizer_agent.run(text)

    elif "plan" in text_lower:
        return planner_agent.run()

    else:
        return capture_agent.run(text)