import logging
from dataclasses import dataclass, field

from app.domain.scenario_models import ScenarioClock
from app.powercontext.client import PowerContextClient
from app.powercontext.runtime import EmbeddedPowerContextMemory, powercontext_config
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

@dataclass
class AppContainer:
    powercontext_client: PowerContextClient
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

    def close(self) -> None:
        self.powercontext_client.close()


def build_disconnected_container() -> AppContainer:
    return AppContainer(
        powercontext_client=PowerContextClient(memory=None),
        llm_client=build_llm_client(),
    )


def build_default_container() -> AppContainer:
    settings = get_settings()
    llm_client = build_llm_client()
    memory: EmbeddedPowerContextMemory | None = None
    try:
        memory = EmbeddedPowerContextMemory(
            config=powercontext_config(settings.powercontext_database_url),
            scope_id=settings.powercontext_scope_id,
            operation_timeout_seconds=settings.powercontext_operation_timeout_seconds,
        )
        SeedingService(memory).seed()
    except Exception as exc:
        logger.warning("PowerContext initialization failed; live mode disabled: %s", exc)
        if memory is not None:
            memory.close()
        memory = None

    return AppContainer(
        powercontext_client=PowerContextClient(memory=memory),
        llm_client=llm_client,
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
