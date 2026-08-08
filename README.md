# crew-ai-blog

Learning project for [CrewAI](https://www.crewai.com/) — small examples of agents, tasks, and crews.

## Initial setup

Dependencies are managed with [uv](https://docs.astral.sh/uv/) (see `pyproject.toml` / `uv.lock`).

```bash
uv sync
```

This creates `.venv` and installs everything automatically — no manual venv activation needed since `uv run` (below) uses it for you.

Create a `.env` file in the project root with at least:

```
OPENAI_API_KEY=your_key_here
```

## Examples

### word-counter

A single-agent crew that checks text.

```bash
cd word-counter
uv run python main.py
```

### interactive-learner

A two-agent crew (`researcher` + `writer`) that researches a topic and writes a blog intro. The researcher uses OpenAI's built-in `web_search` tool via the Responses API, so no extra search API key is needed beyond `OPENAI_API_KEY`.

```bash
cd interactive-learner
uv run python crew.py
```

**Web UI**: a FastAPI server exposes the same crew over the browser, streaming each agent's progress live via Server-Sent Events.

```bash
cd interactive-learner
uv run uvicorn server:app --reload
```

Then open `http://localhost:8000`, enter a topic, and watch the researcher/writer agents work in real time.
