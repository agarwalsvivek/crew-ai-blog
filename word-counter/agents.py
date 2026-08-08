from crewai import Agent
from tools import count_words          # import from your tools file

editor = Agent(
    role="Content Editor",
    goal="Review and improve written content",
    backstory="An experienced editor who checks word counts",
    tools=[count_words],
    verbose=True,
)