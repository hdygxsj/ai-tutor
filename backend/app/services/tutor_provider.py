import json
import math
import ssl
import urllib.error
import urllib.request
from typing import Any, Protocol

from app.core.config import get_settings
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


def build_ssl_context() -> ssl.SSLContext:
    if not get_settings().tutor_ssl_verify:
        return ssl._create_unverified_context()

    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def openai_chat_completions_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/v1"):
        return f"{base}/chat/completions"
    return f"{base}/v1/chat/completions"


class HttpTutorTransport:
    def __init__(self, ssl_context: ssl.SSLContext | None = None) -> None:
        self.ssl_context = ssl_context or build_ssl_context()

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
        with urllib.request.urlopen(request, timeout=30, context=self.ssl_context) as response:
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
            raise TutorProviderError("导师服务返回了无法解析的响应。", 502) from exc
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
            openai_chat_completions_url(base_url),
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
            raise TutorProviderError("导师服务返回了无法解析的响应。", 502) from exc
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
        except urllib.error.HTTPError as exc:
            raise TutorProviderError(self._http_error_message(exc), 502) from exc
        except urllib.error.URLError as exc:
            raise TutorProviderError(self._url_error_message(exc), 502) from exc
        except Exception as exc:
            raise TutorProviderError(
                f"导师服务请求失败：{self._sanitize_error_text(str(exc))}",
                502,
            ) from exc

    def _http_error_message(self, exc: urllib.error.HTTPError) -> str:
        body = exc.read().decode("utf-8", errors="replace")[:300]
        if body:
            return f"导师服务返回 HTTP {exc.code}，请检查 Base URL、模型名与 API Key。详情：{body}"
        return f"导师服务返回 HTTP {exc.code}，请检查 Base URL、模型名与 API Key。"

    def _url_error_message(self, exc: urllib.error.URLError) -> str:
        reason = exc.reason
        if isinstance(reason, ssl.SSLError):
            return (
                "导师服务请求失败：SSL 证书校验未通过。"
                "若使用 Clash/Zeus 等 HTTPS 解密代理，请关闭解密或在 backend/.env 设置 "
                "TUTOR_SSL_VERIFY=false（仅本地调试）。"
            )
        if isinstance(reason, ConnectionRefusedError):
            return "导师服务请求失败：连接被拒绝，请确认 Ollama/接口地址已启动且 Base URL 正确。"
        if isinstance(reason, TimeoutError):
            return "导师服务请求失败：连接超时，请检查网络或 Base URL。"
        return f"导师服务请求失败：{self._sanitize_error_text(str(reason))}"

    def _sanitize_error_text(self, text: str) -> str:
        sanitized = text
        for marker in ("Bearer ", "Authorization:"):
            if marker in sanitized:
                sanitized = sanitized.split(marker, 1)[0].rstrip()
        return sanitized or "未知错误"

    def _parse_reply_content(self, content: Any) -> str:
        if isinstance(content, str) and content.strip():
            return content

        raise TutorProviderError("导师服务返回了无法解析的响应。", 502)

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
