from sqlalchemy.orm import Session

from app.core.tenant import TenantContext
from app.schemas.settings import (
    TutorConnectionTestResponse,
    TutorSettingsResponse,
    TutorSettingsUpdate,
)
from app.services.workspace_settings_store import WorkspaceSettingsStore

TUTOR_SETTINGS_KEY = "tutor"


class TutorSettingsService:
    def __init__(self, db: Session, tenant: TenantContext) -> None:
        self.store = WorkspaceSettingsStore(db, tenant)

    def get_settings(self) -> TutorSettingsResponse:
        return self._to_response(self.get_current_settings())

    def get_current_settings(self) -> TutorSettingsUpdate:
        stored = self.store.get_value(TUTOR_SETTINGS_KEY)
        if stored is None:
            return TutorSettingsUpdate(provider="fake")
        return TutorSettingsUpdate(**stored)

    def save_settings(self, settings: TutorSettingsUpdate) -> TutorSettingsResponse:
        current = self.get_current_settings()
        api_key = settings.api_key if self._has_value(settings.api_key) else current.api_key
        saved = TutorSettingsUpdate(
            provider=settings.provider,
            base_url=settings.base_url,
            model_name=settings.model_name,
            api_key=api_key,
        )
        self.store.save_value(TUTOR_SETTINGS_KEY, saved.model_dump())
        return self._to_response(saved)

    def test_settings(self, settings: TutorSettingsUpdate) -> TutorConnectionTestResponse:
        if settings.provider == "fake":
            return TutorConnectionTestResponse(ok=True, message="Fake tutor provider is ready.")

        if settings.provider == "ollama":
            if not self._has_value(settings.base_url):
                return TutorConnectionTestResponse(
                    ok=False,
                    message="Set base_url before testing the Ollama tutor provider.",
                )
            return TutorConnectionTestResponse(ok=True, message="Ollama tutor settings are valid.")

        missing_fields = [
            field_name
            for field_name, value in (
                ("base_url", settings.base_url),
                ("model_name", settings.model_name),
                ("api_key", self._api_key_for_test(settings)),
            )
            if not self._has_value(value)
        ]
        if missing_fields:
            return TutorConnectionTestResponse(
                ok=False,
                message=f"Set {', '.join(missing_fields)} before testing the tutor provider.",
            )

        return TutorConnectionTestResponse(
            ok=True,
            message="OpenAI-compatible tutor settings are valid.",
        )

    def _to_response(self, settings: TutorSettingsUpdate) -> TutorSettingsResponse:
        return TutorSettingsResponse(
            provider=settings.provider,
            base_url=settings.base_url,
            model_name=settings.model_name,
            has_api_key=self._has_value(settings.api_key),
        )

    def _has_value(self, value: str | None) -> bool:
        return bool(value and value.strip())

    def _api_key_for_test(self, settings: TutorSettingsUpdate) -> str | None:
        if self._has_value(settings.api_key):
            return settings.api_key

        return self.get_current_settings().api_key
