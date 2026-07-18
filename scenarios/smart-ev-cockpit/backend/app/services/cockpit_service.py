from time import perf_counter
from uuid import uuid4

from fastapi import HTTPException

from app.domain.memory_models import MemoryOperation, MemoryRecord
from app.domain.scenario_models import ActRequest, ActResult, ScenarioClock
from app.powermem.client import (
    PowerMemConnectionError,
    PowerMemIngestionError,
    PowerMemResponseError,
)
from app.powermem.queries import build_general_cockpit_query
from app.privacy.projection import project_memory_for_frontend
from app.privacy.scrubber import scrub_text
from app.services.act_router import ActRouter, UnknownActError
from app.services.acts import (
    act_01_profile,
    act_02_multi_actor,
    act_03_routine,
    act_04_capability,
    act_05_location,
    act_06_media,
    act_07_relationship,
    act_08_driving,
    act_09_proactive,
    act_10_lifecycle,
)
from app.services.acts.act_09_proactive import VehicleEvent
from app.services.acts.base import ActContext
from app.services.chat_memory_service import ChatMemoryIngestionResult, ChatMemoryService
from app.services.evidence_service import build_live_evidence
from app.services.lifecycle_service import LifecycleExecutionError
from app.services.llm_service import LlmConnectionError
from app.services.memory_service import MemoryService

UtterRequest = ActRequest


class LifecycleMutationError(Exception):
    def __init__(self, response: dict):
        self.response = response
        super().__init__("Lifecycle mutation failed")

_HANDLERS = {
    "Act 1": act_01_profile.handle,
    "Act 2": act_02_multi_actor.handle,
    "Act 3": act_03_routine.handle,
    "Act 4": act_04_capability.handle,
    "Act 5": act_05_location.handle,
    "Act 6": act_06_media.handle,
    "Act 7": act_07_relationship.handle,
    "Act 8": act_08_driving.handle,
}


def _build_memory_chat_fallback_reply(
    text: str,
    memory_hits: list[MemoryRecord],
) -> str:
    is_chinese = _contains_cjk(text)
    if memory_hits:
        summary = "；".join(memory.content for memory in memory_hits[:3])
        if is_chinese:
            return f"我找到 {len(memory_hits)} 条相关记忆：{summary}"
        return f"I found {len(memory_hits)} relevant memory record(s): {summary}"

    if is_chinese:
        return (
            "我暂时没有找到与这句话直接相关的座舱记忆。"
            "你可以换一种说法，或继续使用十幕演示指令。"
        )
    return (
        "I did not find a directly related cockpit memory. Try rephrasing, "
        "or continue with one of the scripted demo acts."
    )


def _contains_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


class CockpitService:
    def __init__(self, container):
        self.container = container
        self.router = ActRouter()

    def handle_utter(self, request: UtterRequest) -> dict:
        started = perf_counter()
        trace_id = f"trace_{uuid4().hex[:12]}"
        request = self._resolve_request_user_id(request)
        scrubbed = scrub_text(request.text)
        try:
            act_key = self.router.resolve(request.act_key, scrubbed.text)
        except UnknownActError:
            routed_request = request.model_copy(
                update={"act_key": "Chat", "text": scrubbed.text}
            )
            try:
                result = self._handle_chat(routed_request, trace_id)
            except (
                PowerMemConnectionError,
                PowerMemIngestionError,
                PowerMemResponseError,
            ) as powermem_exc:
                raise HTTPException(
                    status_code=503, detail=str(powermem_exc)
                ) from powermem_exc
            except LlmConnectionError as llm_exc:
                raise HTTPException(status_code=503, detail=str(llm_exc)) from llm_exc
            return self._finalize(
                request=routed_request,
                trace_id=trace_id,
                started=started,
                scrubbed=scrubbed,
                result=result,
                vehicle_diff=[],
                persist_chat=True,
            )
        if act_key == "Act 9":
            raise HTTPException(
                status_code=422,
                detail="Act 9 requires POST /events/vehicle with explicit telemetry.",
            )

        routed_request = request.model_copy(
            update={"act_key": act_key, "text": scrubbed.text}
        )
        context = ActContext(request=routed_request, container=self.container)
        try:
            result, lifecycle = self._run_handler(act_key, context, trace_id)
        except (
            PowerMemConnectionError,
            PowerMemIngestionError,
            PowerMemResponseError,
        ) as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except LifecycleExecutionError as exc:
            raise LifecycleMutationError(
                self._finalize_lifecycle_failure(
                    request=routed_request,
                    trace_id=trace_id,
                    started=started,
                    scrubbed=scrubbed,
                    exc=exc,
                    current_day=self.container.scenario_clock.current_day,
                )
            ) from exc

        self._apply_vehicle_context(routed_request)
        vehicle_diff = self._apply_vehicle_patch(act_key, result)
        return self._finalize(
            request=routed_request,
            trace_id=trace_id,
            started=started,
            scrubbed=scrubbed,
            result=result,
            vehicle_diff=vehicle_diff,
            lifecycle=lifecycle,
            persist_chat=True,
        )

    def handle_vehicle_event(self, payload: VehicleEvent) -> dict:
        started = perf_counter()
        trace_id = f"trace_{uuid4().hex[:12]}"
        request = ActRequest(
            act_key="Act 9",
            actor_id="driver_primary",
            user_id="driver_primary",
            seat_position="front_left",
            text=payload.text or "proactive care",
            session_id="vehicle-event",
        )
        scrubbed = scrub_text(request.text)
        context = ActContext(request=request, container=self.container)
        try:
            self.container.powermem_client.require_memory()
            result = act_09_proactive.handle(context, payload)
        except PowerMemConnectionError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        vehicle_diff = self._apply_vehicle_patch("Act 9", result)
        return self._finalize(
            request=request,
            trace_id=trace_id,
            started=started,
            scrubbed=scrubbed,
            result=result,
            vehicle_diff=vehicle_diff,
        )

    def handle_lifecycle(self, payload: ScenarioClock) -> dict:
        started = perf_counter()
        trace_id = f"trace_{uuid4().hex[:12]}"
        request = ActRequest(
            act_key="Act 10",
            actor_id="driver_primary",
            user_id="driver_primary",
            seat_position="front_left",
            text=payload.text or f"lifecycle day {payload.current_day}",
            session_id=f"lifecycle-day-{payload.current_day}",
        )
        scrubbed = scrub_text(request.text)
        context = ActContext(request=request, container=self.container)
        try:
            self.container.powermem_client.require_memory()
            self.container.scenario_clock.current_day = payload.current_day
            result, lifecycle = self._execute_lifecycle(
                context, payload.current_day, trace_id
            )
        except PowerMemConnectionError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except LifecycleExecutionError as exc:
            raise LifecycleMutationError(
                self._finalize_lifecycle_failure(
                    request=request,
                    trace_id=trace_id,
                    started=started,
                    scrubbed=scrubbed,
                    exc=exc,
                    current_day=payload.current_day,
                )
            ) from exc
        return self._finalize(
            request=request,
            trace_id=trace_id,
            started=started,
            scrubbed=scrubbed,
            result=result,
            vehicle_diff=[],
            lifecycle=lifecycle,
        )

    def _finalize(
        self,
        *,
        request: ActRequest,
        trace_id: str,
        started: float,
        scrubbed,
        result: ActResult,
        vehicle_diff: list[dict],
        lifecycle: dict | None = None,
        persist_chat: bool = False,
    ) -> dict:
        act_key = result.act_key
        if persist_chat:
            self._persist_short_term_turn(
                request=request,
                trace_id=trace_id,
                assistant_reply=result.assistant_reply,
            )
        projected_hits = [
            project_memory_for_frontend(hit) for hit in result.memory_hits
        ]
        operations = [
            operation.model_dump(mode="json", exclude_none=True)
            for operation in result.operations
        ]
        selected_memory_ids = list(result.selected_memory_ids)
        if act_key == "Act 1" and not selected_memory_ids:
            selected_memory_ids = [
                memory_id
                for operation in result.operations
                if operation.type == "ADD"
                for memory_id in operation.memory_ids
            ]
        recommendations = [
            recommendation.model_dump(mode="json")
            for recommendation in result.recommendations
        ]
        latency_ms = int((perf_counter() - started) * 1000)
        privacy = {
            "redacted_input": scrubbed.text,
            "redaction_count": scrubbed.redaction_count,
            "tags": scrubbed.tags,
        }
        evidence_request = {
            "session_id": request.session_id,
            "actor_id": request.actor_id,
            "user_id": request.user_id or request.actor_id,
            "seat_position": request.seat_position,
            "act_key": act_key,
        }
        if request.vehicle_context is not None:
            evidence_request["vehicle_context"] = request.vehicle_context.model_dump(
                mode="json"
            )
        evidence = build_live_evidence(
            request=evidence_request,
            privacy=privacy,
            data_source=result.data_source,
            operations=operations,
            memory_hits=projected_hits,
            decision={
                "selected_memory_ids": selected_memory_ids,
                "reason_codes": result.reason_codes,
            },
            vehicle_action={
                "patch": result.vehicle_patch,
                "diff": vehicle_diff,
            },
            recommendations=recommendations,
            lifecycle=lifecycle,
            audit=lifecycle.get("audit") if lifecycle else None,
            latency_ms=latency_ms,
        )
        response = {
            "act_key": act_key,
            "assistant_reply": result.assistant_reply,
            "redacted_input": scrubbed.text,
            "trace_id": trace_id,
            "live_backend": "powermem_sdk",
            "powermem_connected": self.container.powermem_client.is_connected,
            "data_source": result.data_source,
            "operations": operations,
            "memory_hits": projected_hits,
            "selected_memory_ids": selected_memory_ids,
            "vehicle_state": self.container.vehicle_state_service.current_state(),
            "vehicle_state_diff": vehicle_diff,
            "privacy_report": privacy,
            "recommendations": recommendations,
            "evidence": evidence,
        }
        if lifecycle:
            response["lifecycle"] = lifecycle
        self.container.journal_service.append(response)
        return response

    def _run_handler(
        self, act_key: str, context: ActContext, trace_id: str
    ) -> tuple[ActResult, dict | None]:
        if act_key in _HANDLERS:
            return _HANDLERS[act_key](context), None
        if act_key == "Chat":
            return self._handle_chat(context.request, trace_id), None
        self.container.powermem_client.require_memory()
        self.container.scenario_clock.current_day = 90
        return self._execute_lifecycle(context, 90, trace_id)

    def _handle_chat(self, request: ActRequest, trace_id: str) -> ActResult:
        ingestion = ChatMemoryService(self.container.powermem_client).ingest(
            request=request,
            trace_id=trace_id,
        )
        if self.container.llm_client is None:
            return self._handle_memory_chat_fallback(request, ingestion)
        return self._handle_llm_chat(request, ingestion)

    def _handle_llm_chat(
        self,
        request: ActRequest,
        ingestion: ChatMemoryIngestionResult,
    ) -> ActResult:
        llm_client = self.container.llm_client
        if llm_client is None:
            raise LlmConnectionError("LLM chat is not configured for this demo.")

        memory_hits: list[MemoryRecord] = []
        operations: list[MemoryOperation] = [
            MemoryOperation(type="CHAT", result="llm_chat")
        ]
        operations.extend(ingestion.operations)
        memory_hits = self._search_general_chat_memories(request, operations)

        try:
            assistant_reply = llm_client.chat(
                user_text=request.text,
                actor_id=request.actor_id,
                seat_position=request.seat_position,
                vehicle_state=self.container.vehicle_state_service.current_state(),
                memory_hits=[memory.model_dump(mode="json") for memory in memory_hits],
                memory_mutations=ingestion.llm_context(),
            )
        except LlmConnectionError as exc:
            if ingestion.mutations:
                summary = ", ".join(
                    f"{mutation.event}:{mutation.memory_id}"
                    for mutation in ingestion.mutations
                )
                raise LlmConnectionError(
                    "PowerMem mutation succeeded "
                    f"({summary}), but LLM chat generation failed: {exc}"
                ) from exc
            raise
        return ActResult(
            act_key="Chat",
            assistant_reply=assistant_reply,
            memory_hits=memory_hits,
            selected_memory_ids=[memory.memory_id for memory in memory_hits],
            reason_codes=["llm_chat"],
            operations=operations,
            data_source="powermem_sdk+llm",
        )

    def _handle_memory_chat_fallback(
        self,
        request: ActRequest,
        ingestion: ChatMemoryIngestionResult,
    ) -> ActResult:
        operations: list[MemoryOperation] = [
            MemoryOperation(type="CHAT", result="memory_chat_fallback")
        ]
        operations.extend(ingestion.operations)
        memory_hits = self._search_general_chat_memories(request, operations)
        assistant_reply = _build_memory_chat_fallback_reply(request.text, memory_hits)
        return ActResult(
            act_key="Chat",
            assistant_reply=assistant_reply,
            memory_hits=memory_hits,
            selected_memory_ids=[memory.memory_id for memory in memory_hits],
            reason_codes=["memory_chat_fallback"],
            operations=operations,
            data_source="powermem_chat_fallback",
        )

    def _search_general_chat_memories(
        self,
        request: ActRequest,
        operations: list[MemoryOperation],
    ) -> list[MemoryRecord]:
        if not self.container.powermem_client.is_connected:
            return []

        query = build_general_cockpit_query(
            request.text,
            request.actor_id,
            request.seat_position,
            request.user_id,
        )
        memory_hits = MemoryService(self.container.powermem_client).search(
            query=query.query,
            filters=query.filters,
            limit=query.limit,
            user_id=query.user_id,
            prefer_recent_chat=True,
        )
        operations.append(
            MemoryOperation(
                type="SEARCH",
                query=query.query,
                filters=query.filters,
                memory_ids=[memory.memory_id for memory in memory_hits],
            )
        )
        return memory_hits

    def _execute_lifecycle(
        self, context: ActContext, current_day: int, trace_id: str
    ) -> tuple[ActResult, dict]:
        raw = act_10_lifecycle.handle(context, current_day, trace_id)
        memories = [
            MemoryRecord.model_validate(memory) for memory in raw["memory_hits"]
        ]
        operations = [
            {
                **operation,
                "memory_ids": operation.get(
                    "memory_ids", [operation["memory_id"]]
                ),
            }
            for operation in raw["operations"]
        ]
        result = ActResult(
            act_key="Act 10",
            assistant_reply=raw["assistant_reply"],
            memory_hits=memories,
            operations=operations,
        )
        lifecycle = {
            "current_day": raw["current_day"],
            "plan": raw["plan"],
            "completed_operations": raw["completed_operations"],
            "failed_operation": raw["failed_operation"],
            "audit": raw["audit"],
            "trace_id": trace_id,
        }
        return result, lifecycle

    def _finalize_lifecycle_failure(
        self,
        *,
        request: ActRequest,
        trace_id: str,
        started: float,
        scrubbed,
        exc: LifecycleExecutionError,
        current_day: int,
    ) -> dict:
        memories = getattr(exc, "memories", [])
        projected_hits = [
            project_memory_for_frontend(memory) for memory in memories
        ]
        operations = list(exc.audit)
        latency_ms = int((perf_counter() - started) * 1000)
        privacy = {
            "redacted_input": scrubbed.text,
            "redaction_count": scrubbed.redaction_count,
            "tags": scrubbed.tags,
        }
        lifecycle = {
            "current_day": current_day,
            "plan": [
                {
                    "type": item.type,
                    "memory_id": item.memory_id,
                    "memory_ids": [item.memory_id],
                    "before_status": item.before_status,
                    "after_status": item.after_status,
                }
                for item in exc.plan
            ],
            "completed_operations": exc.completed_operations,
            "failed_operation": exc.failed_operation,
            "audit": exc.audit,
            "trace_id": trace_id,
        }
        evidence = build_live_evidence(
            request={
                "session_id": request.session_id,
                "actor_id": request.actor_id,
                "user_id": request.user_id or request.actor_id,
                "seat_position": request.seat_position,
                "act_key": "Act 10",
            },
            privacy=privacy,
            data_source="scenario_seed",
            operations=operations,
            memory_hits=projected_hits,
            decision={"selected_memory_ids": [], "reason_codes": ["lifecycle_mutation_failed"]},
            vehicle_action={"patch": {}, "diff": []},
            lifecycle=lifecycle,
            audit=exc.audit,
            latency_ms=latency_ms,
        )
        response = {
            "act_key": "Act 10",
            "assistant_reply": "Lifecycle execution stopped after a mutation failure.",
            "redacted_input": scrubbed.text,
            "trace_id": trace_id,
            "live_backend": "powermem_sdk",
            "powermem_connected": self.container.powermem_client.is_connected,
            "data_source": "scenario_seed",
            "operations": operations,
            "memory_hits": projected_hits,
            "selected_memory_ids": [],
            "vehicle_state": self.container.vehicle_state_service.current_state(),
            "vehicle_state_diff": [],
            "privacy_report": privacy,
            "recommendations": [],
            "evidence": evidence,
            "lifecycle": lifecycle,
            "completed_operations": exc.completed_operations,
            "failed_operation": exc.failed_operation,
            "audit": exc.audit,
            "current_day": current_day,
        }
        self.container.journal_service.append(response)
        return response

    def _apply_vehicle_patch(self, act_key: str, result: ActResult) -> list[dict]:
        if not result.vehicle_patch:
            return []
        if act_key == "Act 9":
            diff = self.container.vehicle_state_service.apply_event(
                result.vehicle_patch
            )
            result.operations.append(
                MemoryOperation(
                    type="VEHICLE_PATCH",
                    filters={"diff": diff},
                )
            )
            return diff
        return self.container.vehicle_state_service.apply_patch(result.vehicle_patch)

    def _apply_vehicle_context(self, request: ActRequest) -> None:
        if request.vehicle_context is None:
            return
        self.container.vehicle_state_service.apply_patch(
            {
                "hvac": {
                    f"{request.seat_position}_target_temp": (
                        request.vehicle_context.hvac_target_temp_c
                    )
                }
            }
        )

    def _resolve_request_user_id(self, request: ActRequest) -> ActRequest:
        if request.user_id:
            return request
        identity = self.container.identity_service.get_identity(request.actor_id)
        return request.model_copy(update={"user_id": identity.user_id})

    def _persist_short_term_turn(
        self,
        *,
        request: ActRequest,
        trace_id: str,
        assistant_reply: str,
    ) -> None:
        self.container.chat_history_service.append_message(
            session_id=request.session_id,
            actor_id=request.actor_id,
            user_id=request.user_id or request.actor_id,
            seat_position=request.seat_position,
            role="user",
            text=request.text,
            trace_id=trace_id,
        )
        self.container.chat_history_service.append_message(
            session_id=request.session_id,
            actor_id=request.actor_id,
            user_id=request.user_id or request.actor_id,
            seat_position=request.seat_position,
            role="assistant",
            text=assistant_reply,
            trace_id=trace_id,
        )
