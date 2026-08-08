# crew-ai-blog

Learning project for [CrewAI](https://www.crewai.com/) — small examples of agents, tasks, and crews.

## Initial setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root with at least:

```
OPENAI_API_KEY=your_key_here
```

## Examples

### word-counter

A single-agent crew that checks text.

```bash
cd word-counter
python main.py
```

### interactive-learner

A two-agent crew (`researcher` + `writer`) that researches a topic and writes a blog intro. The researcher uses OpenAI's built-in `web_search` tool via the Responses API, so no extra search API key is needed beyond `OPENAI_API_KEY`.

```bash
cd interactive-learner
python crew.py
```
