"""FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.learning_errors import register_learning_errors
from app.api.router import api_router
from app.config import get_allowed_origins


def create_app() -> FastAPI:
    app = FastAPI(
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
        allow_methods=["GET", "POST", "PATCH", "PUT"],
        allow_headers=["Content-Type"],
    )
    register_learning_errors(app)
    app.include_router(api_router)
    return app


app = create_app()
