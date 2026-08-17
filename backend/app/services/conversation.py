"""Shared helpers that turn our generic conversation history — a list of
{"role": "user" | "assistant", "content": str} dicts, oldest first — into
the shape each provider's SDK expects."""

from google.genai import types


def to_chat_messages(prompt: str, history: list[dict] | None = None) -> list[dict]:
    """OpenAI- and Anthropic-compatible `messages` list (both use the same
    {"role": "user"/"assistant", "content": "..."} shape)."""
    messages = [{"role": turn["role"], "content": turn["content"]} for turn in (history or [])]
    messages.append({"role": "user", "content": prompt})
    return messages


def to_gemini_contents(prompt: str, history: list[dict] | None = None) -> list[types.Content]:
    """Gemini's `contents` list — same idea, but the assistant role is
    called "model" instead of "assistant"."""
    contents = [
        types.Content(
            role="model" if turn["role"] == "assistant" else "user",
            parts=[types.Part(text=turn["content"])],
        )
        for turn in (history or [])
    ]
    contents.append(types.Content(role="user", parts=[types.Part(text=prompt)]))
    return contents
