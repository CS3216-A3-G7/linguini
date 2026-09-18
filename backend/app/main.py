"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.learning_errors import register_learning_errors
from app.api.router import api_router
from app.config import get_allowed_origins
from app.database import (
    create_database_engine,
    get_journal_storage,
    get_language_profile_storage,
    get_media_asset_storage,
    get_session_storage,
    get_user_storage,
    get_vocabulary_storage,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_language_profile_storage()
    get_media_asset_storage()
    get_vocabulary_storage()
    get_session_storage()
    get_journal_storage()
    engine = create_database_engine() if get_user_storage() == "postgres" else None
    app.state.database_engine = engine
    try:
        yield
    finally:
        if engine is not None:
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
