from app.schemas.settings import (
    TutorConnectionTestResponse,
    TutorSettingsResponse,
    TutorSettingsUpdate,
)


class TutorSettingsService:
    def __init__(self) -> None:
        self._settings = TutorSettingsUpdate(provider="fake")

    def get_settings(self) -> TutorSettingsResponse:
        return self._to_response(self._settings)

    def get_current_settings(self) -> TutorSettingsUpdate:
        return self._settings

    def save_settings(self, settings: TutorSettingsUpdate) -> TutorSettingsResponse:
        api_key = settings.api_key if self._has_value(settings.api_key) else self._settings.api_key
        self._settings = TutorSettingsUpdate(
            provider=settings.provider,
            base_url=settings.base_url,
            model_name=settings.model_name,
            api_key=api_key,
        )
        return self._to_response(self._settings)

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

        return self._settings.api_key


tutor_settings_service = TutorSettingsService()
