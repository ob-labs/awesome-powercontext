from pydantic import BaseModel, Field


class TraceStep(BaseModel):
    name: str
    status: str
    evidence: dict = Field(default_factory=dict)


class TraceRecord(BaseModel):
    trace_id: str
    request_id: str
    steps: list[TraceStep] = Field(default_factory=list)
