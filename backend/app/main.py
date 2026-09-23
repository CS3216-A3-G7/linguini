"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai import load_ai_settings
from app.api.learning_errors import register_learning_errors
from app.api.router import api_router
from app.config import get_allowed_origins
from app.database import create_database_engine
from app.services.background import ThreadPoolBackgroundRunner


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = create_database_engine()
    app.state.database_engine = engine
    app.state.background_runner = ThreadPoolBackgroundRunner()
    try:
        yield
    finally:
        app.state.background_runner.shutdown(wait=True)
        engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        lifespan=lifespan,
        title="Linguini API",
        version="0.1.0",
        description=(
            "API contracts for Linguini's image-based language-learning sessions "
            "and once-daily journal."
        ),
    )
    app.state.ai_settings = load_ai_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_allowed_origins(),
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
        allow_headers=["Content-Type"],
    )
    register_learning_errors(app)
    app.include_router(api_router)
    return app


app = create_app()
