from crewai import Agent, LLM


# Agents are like classes with a built-in system prompt
# JS analogy: const researcher = new AIWorker({ role, goal, backstory })

# Uses OpenAI's built-in web_search tool via the Responses API,
# so no separate SERPER_API_KEY is needed — only OPENAI_API_KEY.
researcher_llm = LLM(model="gpt-5.4-nano", api="responses", builtin_tools=["web_search"])

researcher = Agent(
    role="Senior Research Analyst",
    goal="find key facts and insights about {topic}",
    backstory="Expert researcher with 10 years experience",
    # tools=[SerperDevTool()],  # web search tool
    llm=researcher_llm,
    verbose=True,           # shows thinking steps
    memory=True,            # remembers past steps
)

writer = Agent(
    role="Content Writer",
    goal="Write a clear, engaging summary from research",
    backstory="Journalist who simplifies complex topics",
    verbose=True,
)
