import json
import math
import urllib.request
from typing import Any, Protocol

from app.schemas.agent import ChatMessage, TokenUsage, TutorChatRequest, TutorChatResponse
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
            reply = (
                f"你提到“{request.message}”。"
                "建议先用一个小例子写出输入、损失和梯度，再继续下一步学习。"
            )
            return TutorChatResponse(
                reply=reply,
                provider=settings.provider,
                usage=self._estimated_usage(settings.provider, "fake", request, reply),
            )

        if settings.provider == "ollama":
            reply, usage = self._ollama_reply(settings, request)
            return TutorChatResponse(
                reply=reply,
                provider=settings.provider,
                usage=usage,
            )

        reply, usage = self._openai_compatible_reply(settings, request)
        return TutorChatResponse(
            reply=reply,
            provider=settings.provider,
            usage=usage,
        )

    def _ollama_reply(
        self,
        settings: TutorSettingsUpdate,
        request: TutorChatRequest,
    ) -> tuple[str, TokenUsage]:
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
            reply = self._parse_reply_content(response["message"]["content"])
        except (KeyError, TypeError) as exc:
            raise TutorProviderError("Tutor provider returned an invalid response.", 502) from exc
        return reply, self._ollama_usage(settings.provider, model_name, response)

    def _openai_compatible_reply(
        self,
        settings: TutorSettingsUpdate,
        request: TutorChatRequest,
    ) -> tuple[str, TokenUsage]:
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
            reply = self._parse_reply_content(response["choices"][0]["message"]["content"])
        except (IndexError, KeyError, TypeError) as exc:
            raise TutorProviderError("Tutor provider returned an invalid response.", 502) from exc
        return reply, self._openai_usage(settings.provider, model_name, response)

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

    def _estimated_usage(
        self,
        provider: str,
        model: str,
        request: TutorChatRequest,
        reply: str,
    ) -> TokenUsage:
        prompt_chars = sum(len(message["content"]) for message in self._messages(request))
        completion_chars = len(reply)
        prompt_tokens = math.ceil(prompt_chars * (2 / 3))
        completion_tokens = math.ceil(completion_chars * 0.75)
        return TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            provider=provider,
            model=model,
            source="estimated",
        )

    def _openai_usage(self, provider: str, model: str, response: dict[str, Any]) -> TokenUsage:
        usage = response.get("usage")
        if not isinstance(usage, dict):
            return self._unknown_usage(provider, model)

        prompt_tokens = self._safe_token_count(usage.get("prompt_tokens"))
        completion_tokens = self._safe_token_count(usage.get("completion_tokens"))
        total_tokens = self._safe_token_count(usage.get("total_tokens"))
        if total_tokens == 0:
            total_tokens = prompt_tokens + completion_tokens
        return TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            provider=provider,
            model=model,
            source="provider",
        )

    def _ollama_usage(self, provider: str, model: str, response: dict[str, Any]) -> TokenUsage:
        if "prompt_eval_count" not in response and "eval_count" not in response:
            return self._unknown_usage(provider, model)

        prompt_tokens = self._safe_token_count(response.get("prompt_eval_count"))
        completion_tokens = self._safe_token_count(response.get("eval_count"))
        return TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            provider=provider,
            model=model,
            source="provider",
        )

    def _unknown_usage(self, provider: str, model: str) -> TokenUsage:
        return TokenUsage(
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            provider=provider,
            model=model,
            source="unknown",
        )

    def _safe_token_count(self, value: object) -> int:
        return value if isinstance(value, int) and value >= 0 else 0

    def _require(self, value: str | None, provider: str, field_name: str) -> str:
        if value and value.strip():
            return value

        raise TutorProviderError(
            f"Missing tutor provider setting for {provider}: {field_name}.",
            400,
        )
