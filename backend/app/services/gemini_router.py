from typing import Literal

from google import genai
from google.genai import types
from pydantic import BaseModel

SYSTEM_INSTRUCTION = """You are HubAI's routing orchestrator. Your sole job is to analyze a user prompt and decide which AI provider is best suited for it.

Available providers:
- "openai" - general reasoning, coding, writing, analysis
- "claude" - long-form writing, nuanced analysis, document review
- "gemini" - multimodal tasks, Google ecosystem queries, broad Q&A
- "midjourney" - artistic image generation, stylized visuals
- "dalle" - photorealistic or illustrative image generation

Rules:
1. Choose exactly ONE provider that best fits the user's intent.
2. Rewrite the user's prompt into a clear, optimized "refined_prompt" for that provider.
3. Include a brief "reasoning" explaining why you chose that provider."""


class GeminiRouteResult(BaseModel):
    provider: Literal["openai", "claude", "gemini", "midjourney", "dalle"]
    refined_prompt: str
    reasoning: str


async def route_with_gemini(
    prompt: str, api_key: str, model: str = "gemini-2.5-flash"
) -> GeminiRouteResult:
    """Ask Gemini to pick the best provider for `prompt` and refine it accordingly."""
    client = genai.Client(api_key=api_key)

    response = await client.aio.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=GeminiRouteResult,
        ),
    )

    if response.parsed is None:
        raise ValueError(f"Gemini returned an unparsable response: {response.text!r}")

    return response.parsed
