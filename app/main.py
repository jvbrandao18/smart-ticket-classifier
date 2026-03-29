from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.audit import router as audit_router
from app.api.routes.classify import router as classify_router
from app.api.routes.examples import router as examples_router
from app.api.routes.health import router as health_router
from app.api.routes.metrics import router as metrics_router
from app.core.config import Settings, get_settings
from app.core.database import create_engine_and_session_factory
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import register_middlewares
from app.infra.repositories.audit_repository import AuditRepository
from app.infra.repositories.ticket_repository import TicketRepository
from app.services.audit_service import AuditService
from app.services.classification_service import ClassificationService
from app.services.llm_classifier import LLMClassifier
from app.services.metrics_service import MetricsService


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    configure_logging(app_settings.log_level)

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        engine, session_factory = create_engine_and_session_factory(app_settings.database_url)
        application.state.engine = engine
        application.state.session_factory = session_factory
        yield
        engine.dispose()

    ticket_repository = TicketRepository()
    audit_repository = AuditRepository()
    application = FastAPI(
        title=app_settings.app_name,
        version=app_settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    application.state.settings = app_settings
    application.state.classification_service = ClassificationService(
        settings=app_settings,
        llm_classifier=LLMClassifier(settings=app_settings),
        ticket_repository=ticket_repository,
        audit_repository=audit_repository,
    )
    application.state.audit_service = AuditService(
        ticket_repository=ticket_repository,
        audit_repository=audit_repository,
    )
    application.state.metrics_service = MetricsService(
        ticket_repository=ticket_repository,
        audit_repository=audit_repository,
    )

    register_middlewares(application)
    register_exception_handlers(application)
    application.include_router(audit_router)
    application.include_router(health_router)
    application.include_router(classify_router)
    application.include_router(examples_router)
    application.include_router(metrics_router)
    return application


app = create_app()
