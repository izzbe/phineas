import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

_STATIC = Path(__file__).parent / "static"

from .agent import run_backtest
from .sandbox import fetch_schema
from .schemas import BacktestJobResponse, BacktestRequest, JobStatus


class _Job:
    def __init__(self):
        self.status: JobStatus = JobStatus.pending
        self.events: list[dict] = []
        self.result: Optional[Any] = None
        self.error: Optional[str] = None
        self.done: bool = False
        self.task: Optional[asyncio.Task] = None


_jobs: dict[str, _Job] = {}


async def _run(job_id: str, request: BacktestRequest):
    job = _jobs[job_id]
    job.status = JobStatus.running
    last_stdout = ""
    try:
        async for event in run_backtest(request):
            job.events.append(event)
            if event["type"] == "code_output":
                last_stdout = event.get("stdout", "")
        job.status = JobStatus.completed
        for line in reversed(last_stdout.strip().splitlines()):
            try:
                job.result = json.loads(line)
                break
            except Exception:
                pass
    except Exception as e:
        job.error = str(e)
        job.status = JobStatus.failed
        job.events.append({"type": "agent_error", "content": str(e)})
    finally:
        job.events.append({"type": "stream_end"})
        job.done = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    await fetch_schema()
    yield
    for job in _jobs.values():
        if job.task and not job.task.done():
            job.task.cancel()


app = FastAPI(title="Phineas", lifespan=lifespan)


@app.post("/backtest", response_model=BacktestJobResponse)
async def create_backtest(request: BacktestRequest):
    job_id = str(uuid.uuid4())
    job = _Job()
    _jobs[job_id] = job
    job.task = asyncio.create_task(_run(job_id, request))
    return BacktestJobResponse(job_id=job_id, status=JobStatus.pending)


@app.get("/backtest/{job_id}", response_model=BacktestJobResponse)
async def get_backtest(job_id: str):
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return BacktestJobResponse(
        job_id=job_id,
        status=job.status,
        result=job.result,
        error=job.error,
    )


@app.get("/backtest/{job_id}/stream")
async def stream_backtest(job_id: str):
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    async def generate():
        idx = 0
        while True:
            while idx < len(job.events):
                event = job.events[idx]
                idx += 1
                yield f"event: {event['type']}\ndata: {json.dumps(event)}\n\n"
                if event["type"] == "stream_end":
                    return
            if job.done and idx >= len(job.events):
                return
            await asyncio.sleep(0.05)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/")
async def frontend():
    return FileResponse(_STATIC / "index.html")


@app.get("/api/status")
async def status():
    return {"service": "phineas", "version": "0.1.0"}
