from crewai import Task
from agents import researcher, writer

research_task = Task(
    description="Research {topic} and find 3-5 key insights.",
    expected_output="A bullet list of key facts and insights",
    agent=researcher,   # who does this task
)

writer_task = Task(
    description="Write a 150-word blog intro about {topic}.",
    expected_output="An engaging blog introduction paragraph",
    agent=writer,
    context=[research_task],  # depends on research_task output
    # JS analogy: await research_task → feeds into this
)