from app.services.tutor_provider import openai_chat_completions_url


def test_openai_chat_completions_url_appends_v1_when_missing() -> None:
    assert (
        openai_chat_completions_url("https://api.deepseek.com")
        == "https://api.deepseek.com/v1/chat/completions"
    )


def test_openai_chat_completions_url_keeps_existing_v1_suffix() -> None:
    assert (
        openai_chat_completions_url("https://llm.example.test/v1/")
        == "https://llm.example.test/v1/chat/completions"
    )
