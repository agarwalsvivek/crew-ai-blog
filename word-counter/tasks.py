from crewai import Task
from agents import editor              # import from your agents file

check_task = Task(
    description="Count the words in: '{text}'",
    expected_output="A word count result",
    agent=editor,
)