from crewai import Crew, Process
from agents import researcher, writer
from tasks import research_task, writer_task

import os
from dotenv import load_dotenv

def load_api_key():
    load_dotenv(override=True)
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print(f"OpenAI API key detected: {api_key[:8]}...")
    else:
        print("OpenAI API key not set. See setup/troubleshooting guide.")

load_api_key()

# Crew wires agents and tasks together
# JS analogy: like app.listen() — kicks off the whole thing


crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writer_task],
    process=Process.sequential,   # tasks run in order
    verbose=True
)

result = crew.kickoff(inputs={"topic":"AI in healthcare"})
print(result)