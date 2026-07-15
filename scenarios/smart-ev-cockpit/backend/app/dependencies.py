import logging
from dataclasses import dataclass, field

from powermem import create_memory

from app.domain.scenario_models import ScenarioClock
from app.powermem.client import PowerMemClient
from app.services.chat_history_service import ChatHistoryService
from app.services.identity_service import IdentityService
from app.services.llm_service import OpenAICompatibleLlmClient
from app.services.operation_journal_service import OperationJournalService
from app.services.seeding_service import SeedingService
from app.services.test_data_service import TestDataService
from app.services.trace_service import TraceService
from app.services.vehicle_state_service import VehicleStateService
from app.settings import get_settings

logger = logging.getLogger(__name__)

POWERMEM_EMBEDDING_TIMEOUT_SECONDS = 30.0
POWERMEM_EMBEDDING_MAX_RETRIES = 0


@dataclass
class AppContainer:
    powermem_client: PowerMemClient
    llm_client: object | None = None
    trace_service: TraceService = field(default_factory=TraceService)
    journal_service: OperationJournalService = field(default_factory=OperationJournalService)
    vehicle_state_service: VehicleStateService = field(default_factory=VehicleStateService)
    scenario_clock: ScenarioClock = field(default_factory=ScenarioClock)
    test_data_service: TestDataService = field(default_factory=TestDataService)
    chat_history_service: ChatHistoryService = field(
        default_factory=lambda: ChatHistoryService(get_settings().chat_history_db_path)
    )
    identity_service: IdentityService = field(
        default_factory=lambda: IdentityService(get_settings().identity_db_path)
    )


def build_disconnected_container() -> AppContainer:
    return AppContainer(powermem_client=PowerMemClient(memory=None), llm_client=build_llm_client())


def build_default_container() -> AppContainer:
    llm_client = build_llm_client()
    try:
        memory = create_memory()
        _limit_embedding_request_duration(memory)
        SeedingService(memory).seed()
    except Exception as exc:
        logger.warning("PowerMem initialization failed; live mode disabled: %s", exc)
        memory = None

    return AppContainer(powermem_client=PowerMemClient(memory=memory), llm_client=llm_client)


def _limit_embedding_request_duration(memory) -> None:
    embedding = getattr(memory, "embedding", None)
    client = getattr(embedding, "client", None)
    with_options = getattr(client, "with_options", None)
    if not callable(with_options):
        return

    embedding.client = with_options(
        timeout=POWERMEM_EMBEDDING_TIMEOUT_SECONDS,
        max_retries=POWERMEM_EMBEDDING_MAX_RETRIES,
    )


def build_llm_client() -> OpenAICompatibleLlmClient | None:
    settings = get_settings()
    if settings.llm_provider != "openai":
        logger.warning("Unsupported LLM provider %s; chat disabled", settings.llm_provider)
        return None
    if not settings.llm_model or not settings.openai_llm_base_url:
        return None
    return OpenAICompatibleLlmClient(
        provider=settings.llm_provider,
        model=settings.llm_model,
        base_url=settings.openai_llm_base_url,
        api_key=settings.llm_api_key,
    )


def override_container(container: AppContainer) -> AppContainer:
    return container
