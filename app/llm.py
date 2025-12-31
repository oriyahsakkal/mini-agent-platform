import hashlib

SUPPORTED_MODELS: set[str] = {"gpt-4o"}


def mock_llm_complete(model: str, prompt: str) -> str:
    """
    Deterministic mock LLM completion.

    Generates a stable response by hashing the model and prompt,
    ensuring predictable behavior for tests without external API calls.
    """
    if model not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported model: {model}")

    digest = hashlib.sha256(f"{model}::{prompt}".encode("utf-8")).hexdigest()[:16]
    return f"[mock:{model}] digest={digest} | response=OK"
