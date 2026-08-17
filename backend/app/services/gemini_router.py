from typing import Literal

from google import genai
from google.genai import types
from pydantic import BaseModel

from app.services.conversation import to_gemini_contents

SYSTEM_INSTRUCTION = """You are HubAI's routing orchestrator. Your job is to look at the user's latest message — optionally with prior conversation turns for context — and decide which AI provider is best suited to answer it.

Available providers:
- "openai" - general reasoning, coding, writing, analysis
- "claude" - long-form writing, nuanced analysis, document review
- "gemini" - multimodal tasks, Google ecosystem queries, broad Q&A
- "midjourney" - artistic image generation, stylized visuals
- "dalle" - photorealistic or illustrative image generation

Rules:
1. Choose exactly ONE provider that best fits the user's latest message.
2. Rewrite the user's latest message into a clear, optimized "refined_prompt" for that provider. If there is prior conversation history, use it to resolve pronouns and references ("it", "that", "him", "the previous one", etc.) so the refined_prompt is fully SELF-CONTAINED and makes sense on its own.
3. Include a brief "reasoning" explaining why you chose that provider."""


class GeminiRouteResult(BaseModel):
    provider: Literal["openai", "claude", "gemini", "midjourney", "dalle"]
    refined_prompt: str
    reasoning: str


async def route_with_gemini(
    prompt: str,
    api_key: str,
    model: str = "gemini-flash-lite-latest",
    history: list[dict] | None = None,
) -> GeminiRouteResult:
    """Ask Gemini to pick the best provider for `prompt` — optionally aware
    of prior conversation `history` — and refine it accordingly."""
    client = genai.Client(api_key=api_key)

    response = await client.aio.models.generate_content(
        model=model,
        contents=to_gemini_contents(prompt, history),
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=GeminiRouteResult,
        ),
    )

    if response.parsed is None:
        raise ValueError(f"Gemini returned an unparsable response: {response.text!r}")

    return response.parsed
