from fastapi import FastAPI

from app.api.routes.classify import router as classify_router
from app.api.routes.health import router as health_router
from app.core.config import Settings, get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import register_middlewares
from app.services.classification_service import ClassificationService
from app.services.llm_classifier import LLMClassifier


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    configure_logging(app_settings.log_level)

    application = FastAPI(
        title=app_settings.app_name,
        version=app_settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    application.state.settings = app_settings
    application.state.classification_service = ClassificationService(
        settings=app_settings,
        llm_classifier=LLMClassifier(settings=app_settings),
    )

    register_middlewares(application)
    register_exception_handlers(application)
    application.include_router(health_router)
    application.include_router(classify_router)
    return application


app = create_app()
