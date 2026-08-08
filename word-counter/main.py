from crewai import Crew, Process
from agents import editor
from tasks import check_task

from dotenv import load_dotenv
load_dotenv()

crew = Crew(
    agents=[editor],
    tasks=[check_task],
    process=Process.sequential,
)

result = crew.kickoff(inputs={"text": "Hello world this is a test"})
print(result)