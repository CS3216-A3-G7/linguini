"""Environment configuration for the temporary demo integration."""

import os
from pathlib import Path
from uuid import UUID

DEMO_USERS_PATH = Path(__file__).parent / "data" / "users.json"
DEFAULT_DEMO_USER_ID = "11111111-1111-4111-8111-111111111111"


def get_demo_user_id() -> UUID:
    return UUID(os.getenv("DEMO_USER_ID", DEFAULT_DEMO_USER_ID))


def get_allowed_origins() -> list[str]:
    return [
        origin.strip()
        for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]
