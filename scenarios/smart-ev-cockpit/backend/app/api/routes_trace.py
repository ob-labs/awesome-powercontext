from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/scenarios/smart-ev-cockpit")


@router.get("/traces")
def traces(request: Request) -> dict:
    return {
        "traces": [
            trace.model_dump(mode="json")
            for trace in request.app.state.container.trace_service.list()
        ]
    }


@router.get("/export")
def export_trace_data(request: Request) -> dict:
    return {"recent_operations": request.app.state.container.journal_service.recent(limit=100)}
