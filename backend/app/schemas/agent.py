from typing import Literal

from pydantic import BaseModel, Field, field_validator

ChatRole = Literal["system", "user", "assistant"]


class ChatMessage(BaseModel):
    role: ChatRole
    content: str


class TutorChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: list[ChatMessage] = Field(default_factory=list)
    course_id: str | None = None
    session_id: str | None = None

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            msg = "message must not be blank"
            raise ValueError(msg)
        return value


class TutorChatResponse(BaseModel):
    reply: str
    provider: str
    usage: "TokenUsage"
    actions: list["AgentAction"] = Field(default_factory=list)
    course_id: str | None = None
    session_id: str | None = None


class TokenUsage(BaseModel):
    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    provider: str
    model: str | None = None
    source: str


class AgentAction(BaseModel):
    type: str
    label: str
    payload: dict[str, object] = Field(default_factory=dict)
