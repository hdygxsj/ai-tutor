import json
import urllib.request
from typing import Any, Protocol

from app.schemas.agent import ChatMessage, TutorChatRequest, TutorChatResponse
from app.schemas.settings import TutorSettingsUpdate
from app.services.tutor_settings_service import TutorSettingsService

SYSTEM_PROMPT = "你是 AI Dream 的机器学习导师，用中文简洁回答，并给出下一步学习建议。"


class TutorProviderError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class TutorTransport(Protocol):
    def post_json(
        self,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]: ...


class HttpTutorTransport:
    def post_json(
        self,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", **(headers or {})},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))


class TutorProviderService:
    def __init__(
        self,
        settings_service: TutorSettingsService,
        transport: TutorTransport | None = None,
    ) -> None:
        self.settings_service = settings_service
        self.transport = transport or HttpTutorTransport()

    def reply(self, request: TutorChatRequest) -> TutorChatResponse:
        settings = self.settings_service.get_current_settings()

        if settings.provider == "fake":
            return TutorChatResponse(
                reply=(
                    f"你提到“{request.message}”。"
                    "建议先用一个小例子写出输入、损失和梯度，再继续下一步学习。"
                ),
                provider=settings.provider,
            )

        if settings.provider == "ollama":
            return TutorChatResponse(
                reply=self._ollama_reply(settings, request),
                provider=settings.provider,
            )

        return TutorChatResponse(
            reply=self._openai_compatible_reply(settings, request),
            provider=settings.provider,
        )

    def _ollama_reply(self, settings: TutorSettingsUpdate, request: TutorChatRequest) -> str:
        base_url = self._require(settings.base_url, settings.provider, "base_url")
        model_name = self._require(settings.model_name, settings.provider, "model_name")
        response = self._post_json(
            f"{base_url.rstrip('/')}/api/chat",
            {
                "model": model_name,
                "messages": self._messages(request),
                "stream": False,
            },
        )
        try:
            return self._parse_reply_content(response["message"]["content"])
        except (KeyError, TypeError) as exc:
            raise TutorProviderError("Tutor provider returned an invalid response.", 502) from exc

    def _openai_compatible_reply(
        self,
        settings: TutorSettingsUpdate,
        request: TutorChatRequest,
    ) -> str:
        base_url = self._require(settings.base_url, settings.provider, "base_url")
        model_name = self._require(settings.model_name, settings.provider, "model_name")
        api_key = self._require(settings.api_key, settings.provider, "api_key")
        response = self._post_json(
            f"{base_url.rstrip('/')}/chat/completions",
            {
                "model": model_name,
                "messages": self._messages(request),
                "temperature": 0.2,
            },
            {"Authorization": f"Bearer {api_key}"},
        )
        try:
            return self._parse_reply_content(response["choices"][0]["message"]["content"])
        except (IndexError, KeyError, TypeError) as exc:
            raise TutorProviderError("Tutor provider returned an invalid response.", 502) from exc

    def _post_json(
        self,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        try:
            return self.transport.post_json(url, payload, headers)
        except TutorProviderError:
            raise
        except Exception as exc:
            raise TutorProviderError("Tutor provider request failed.", 502) from exc

    def _parse_reply_content(self, content: Any) -> str:
        if isinstance(content, str) and content.strip():
            return content

        raise TutorProviderError("Tutor provider returned an invalid response.", 502)

    def _messages(self, request: TutorChatRequest) -> list[dict[str, str]]:
        messages = [ChatMessage(role="system", content=SYSTEM_PROMPT), *request.history]
        messages.append(ChatMessage(role="user", content=request.message))
        return [message.model_dump() for message in messages]

    def _require(self, value: str | None, provider: str, field_name: str) -> str:
        if value and value.strip():
            return value

        raise TutorProviderError(
            f"Missing tutor provider setting for {provider}: {field_name}.",
            400,
        )
