from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_health import router as health_router
from app.api.routes_identity import router as identity_router
from app.api.routes_memory import router as memory_router
from app.api.routes_scenario import router as scenario_router
from app.api.routes_test_data import router as test_data_router
from app.api.routes_trace import router as trace_router
from app.api.routes_vehicle import router as vehicle_router
from app.dependencies import (
    AppContainer,
    build_default_container,
    build_disconnected_container,
)


def create_app(
    container: AppContainer | None = None,
    bootstrap_powercontext: bool = False,
) -> FastAPI:
    lifespan = None
    if bootstrap_powercontext:

        @asynccontextmanager
        async def startup_lifespan(app: FastAPI) -> AsyncIterator[None]:
            owns_container = container is None
            if container is None:
                app.state.container = build_default_container()
            try:
                yield
            finally:
                if owns_container:
                    app.state.container.close()

        lifespan = startup_lifespan

    app = FastAPI(
        title="Smart EV Cockpit Memory API",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.container = container or build_disconnected_container()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(identity_router)
    app.include_router(scenario_router)
    app.include_router(memory_router)
    app.include_router(vehicle_router)
    app.include_router(trace_router)
    app.include_router(test_data_router)
    return app


app = create_app(bootstrap_powercontext=True)
