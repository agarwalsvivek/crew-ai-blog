import asyncio
import json
import queue          # thread-safe queue — like a channel to pass messages between threads
import threading       # JS analogy: real OS threads. Node doesn't need this (single-threaded
                        # event loop) but Python's crew.kickoff() below is blocking/synchronous,
                        # so it must run on its own thread or it would freeze the whole server.
from pathlib import Path  # like Node's `path` module, but object-oriented (Path(...) / "sub")

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from crewai.events import crewai_event_bus
from crewai.events.types.agent_events import (
    AgentExecutionCompletedEvent,
    AgentExecutionStartedEvent,
)
from crewai.events.types.task_events import TaskCompletedEvent
from crewai.events.types.tool_usage_events import (
    ToolUsageFinishedEvent,
    ToolUsageStartedEvent,
)

# Python's `import` == JS's `import { x } from "y"`. No default exports —
# everything is named, and there's no bundler/transpile step involved.
from crew import build_crew, load_api_key

# __file__ = path of this file (like import.meta.url in JS). .parent = its
# containing dir. The `/` operator is Path's way of joining paths (like path.join).
STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI()  # JS analogy: const app = express()
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")  # like express.static()

# Single-run guard: crewai_event_bus is a process-wide singleton, so
# scoped_handlers() below isn't safe for two concurrent kickoffs.
# threading.Lock() is a mutex — needed because two real threads could touch
# this at once. Plain JS doesn't need this since only one thing runs at a time.
_run_lock = threading.Lock()


# @app.on_event(...) is a decorator — Python's way of wrapping a function to
# register it, roughly like Express middleware/hooks but as `@` syntax above
# the function instead of a call like app.on('startup', fn).
@app.on_event("startup")
def on_startup() -> None:  # `-> None` is a type hint (like TS `: void`), not enforced at runtime
    load_api_key()


@app.get("/")  # JS analogy: app.get("/", (req, res) => ...)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


def _sse(event: str, data: dict) -> str:
    # f"..." is a Python f-string == JS template literal `${}`.
    # `dict` here is like a plain JS object; json.dumps == JSON.stringify.
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@app.get("/api/run/stream")
async def run_stream(topic: str) -> StreamingResponse:  # `topic` comes from ?topic=... query string
    # acquire(blocking=False) tries to grab the lock without waiting; returns
    # False immediately if someone else already holds it (instead of blocking).
    if not _run_lock.acquire(blocking=False):
        # A function containing `yield` is a generator, same concept as a JS
        # `function*` — calling it doesn't run the body, it hands back an
        # iterator that produces values one at a time when pulled.
        async def busy():
            yield _sse("error", {"message": "A run is already in progress. Try again once it finishes."})

        return StreamingResponse(busy(), media_type="text/event-stream")

    # Type hint in quotes ("queue.Queue[...]") is just documenting the shape,
    # like a TS generic Queue<[string | null, object | null]>. Python doesn't
    # check this at runtime — it's purely for readers/editors.
    events_queue: "queue.Queue[tuple[str | None, dict | None]]" = queue.Queue()

    # These nested functions are closures over `events_queue`, same as JS
    # closures — they "remember" the surrounding scope even when called later
    # from inside crewai's event bus.
    def on_agent_started(source, event: AgentExecutionStartedEvent) -> None:
        events_queue.put(("log", {"message": f"{event.agent.role} started working..."}))

    def on_agent_completed(source, event: AgentExecutionCompletedEvent) -> None:
        events_queue.put(("log", {"message": f"{event.agent.role} finished."}))

    def on_tool_started(source, event: ToolUsageStartedEvent) -> None:
        role = event.agent_role or "agent"  # `or` here works like JS `||` for a fallback value
        events_queue.put(("log", {"message": f"{role} is using tool '{event.tool_name}'..."}))

    def on_tool_finished(source, event: ToolUsageFinishedEvent) -> None:
        events_queue.put(("log", {"message": f"Tool '{event.tool_name}' finished."}))

    def on_task_completed(source, event: TaskCompletedEvent) -> None:
        raw = (event.output.raw or "") if event.output else ""
        # raw[:200] is Python slicing — like raw.slice(0, 200) in JS.
        preview = raw[:200] + ("..." if len(raw) > 200 else "")
        events_queue.put(("log", {"message": f"Task completed: {preview}"}))

    # This is the function that actually runs on the background thread
    # (see threading.Thread(...) below) — it does the slow, blocking work.
    def worker() -> None:
        try:
            # `with ... :` is a context manager, like JS's `using` — it runs
            # setup code, then guarantees cleanup code runs after the block,
            # even if an exception is thrown inside it.
            with crewai_event_bus.scoped_handlers():
                # Registers each handler function against an event type —
                # like eventBus.on("agentStarted", onAgentStarted) in JS.
                crewai_event_bus.on(AgentExecutionStartedEvent)(on_agent_started)
                crewai_event_bus.on(AgentExecutionCompletedEvent)(on_agent_completed)
                crewai_event_bus.on(ToolUsageStartedEvent)(on_tool_started)
                crewai_event_bus.on(ToolUsageFinishedEvent)(on_tool_finished)
                crewai_event_bus.on(TaskCompletedEvent)(on_task_completed)

                crew = build_crew()
                result = crew.kickoff(inputs={"topic": topic})  # blocking call — this is why we need a thread
            events_queue.put(("result", {"output": str(result)}))
        except Exception as exc:  # JS analogy: catch (exc)
            events_queue.put(("error", {"message": str(exc)}))
        finally:  # always runs, whether the try succeeded or raised — same as JS finally
            events_queue.put((None, None))  # sentinel telling the reader below "no more events"
            _run_lock.release()

    # Spawn a real OS thread and start it immediately. `daemon=True` means it
    # won't stop the server process from exiting if it's still running.
    threading.Thread(target=worker, daemon=True).start()

    # This generator is what actually streams the HTTP response body, one
    # chunk at a time, similar to writing to a Node `Response` stream.
    async def event_generator():
        loop = asyncio.get_event_loop()
        while True:
            # events_queue.get() is a *blocking* call (it waits for an item).
            # run_in_executor offloads that wait to a worker thread so it
            # doesn't freeze the async event loop while waiting — same idea
            # as not wanting to block Node's event loop with sync I/O.
            event_name, data = await loop.run_in_executor(None, events_queue.get)
            if event_name is None:  # hit the sentinel from worker()'s `finally` — we're done
                break
            yield _sse(event_name, data)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
