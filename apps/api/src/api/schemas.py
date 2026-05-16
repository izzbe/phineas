import uuid
from datetime import date
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class BacktestRequest(BaseModel):
    strategy: str
    start_date: date = Field(default=date(2010, 1, 1))
    end_date: date = Field(default=date(2023, 12, 31))
    initial_capital: float = Field(default=1_000_000.0)


class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class BacktestJobResponse(BaseModel):
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: JobStatus
    result: Optional[Any] = None
    error: Optional[str] = None
