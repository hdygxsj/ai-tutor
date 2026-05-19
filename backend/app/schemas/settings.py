from typing import Literal

from pydantic import BaseModel

TutorProvider = Literal["fake", "ollama", "openai_compatible"]


class TutorSettingsUpdate(BaseModel):
    provider: TutorProvider
    base_url: str | None = None
    model_name: str | None = None
    api_key: str | None = None


class TutorSettingsResponse(BaseModel):
    provider: TutorProvider
    base_url: str | None = None
    model_name: str | None = None
    has_api_key: bool


class TutorConnectionTestResponse(BaseModel):
    ok: bool
    message: str
