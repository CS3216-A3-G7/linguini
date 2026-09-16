"""FastAPI application entrypoint."""

from fastapi import FastAPI

from app.api.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Linguini API",
        version="0.1.0",
        description=(
            "API contracts for Linguini's image-based language-learning sessions "
            "and once-daily journal."
        ),
    )
    app.include_router(api_router)
    return app


app = create_app()
