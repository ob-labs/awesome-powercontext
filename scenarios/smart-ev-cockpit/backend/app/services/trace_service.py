from app.domain.trace_models import TraceRecord, TraceStep


class TraceService:
    def __init__(self):
        self._traces: dict[str, TraceRecord] = {}

    def create_trace(self, trace_id: str, request_id: str) -> TraceRecord:
        trace = TraceRecord(trace_id=trace_id, request_id=request_id)
        self._traces[trace_id] = trace
        return trace

    def add_step(self, trace_id: str, name: str, status: str, evidence: dict) -> TraceRecord:
        trace = self._traces[trace_id]
        trace.steps.append(TraceStep(name=name, status=status, evidence=evidence))
        return trace

    def get(self, trace_id: str) -> TraceRecord | None:
        return self._traces.get(trace_id)

    def list(self) -> list[TraceRecord]:
        return list(self._traces.values())
