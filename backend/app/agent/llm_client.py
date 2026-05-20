from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from app.agent.prompts import build_planner_prompt, build_response_prompt


class BaseLLMClient:
    """Provider-neutral LLM interface for planning and response generation."""

    def generate_plan(
        self,
        *,
        query: str,
        schema: list[dict[str, Any]],
        recent_messages: list[dict[str, Any]],
        intent: str,
    ) -> dict[str, Any]:
        """Return a structured plan for the current query."""
        raise NotImplementedError

    def generate_response(
        self,
        *,
        query: str,
        schema: list[dict[str, Any]],
        analysis_plan: list[str],
        tool_result: dict[str, Any],
        chart_url: str | None = None,
        error: str | None = None,
        follow_up_questions: list[str] | None = None,
    ) -> str | dict[str, Any]:
        """Return a final answer based only on already-computed tool output."""
        raise NotImplementedError


class NoOpLLMClient(BaseLLMClient):
    """LLM client used when LLM is disabled or not fully configured."""

    def __init__(self, reason: str = "LLM is not configured") -> None:
        self.reason = reason

    def generate_plan(
        self,
        *,
        query: str,
        schema: list[dict[str, Any]],
        recent_messages: list[dict[str, Any]],
        intent: str,
    ) -> dict[str, Any]:
        """Raise a clear error instead of attempting an LLM request."""
        raise RuntimeError(self.reason)

    def generate_response(
        self,
        *,
        query: str,
        schema: list[dict[str, Any]],
        analysis_plan: list[str],
        tool_result: dict[str, Any],
        chart_url: str | None = None,
        error: str | None = None,
        follow_up_questions: list[str] | None = None,
    ) -> str | dict[str, Any]:
        """Raise a clear error instead of attempting an LLM request."""
        raise RuntimeError(self.reason)


class OpenAICompatibleLLMClient(BaseLLMClient):
    """Small OpenAI-compatible chat completions client using the standard library."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: int = 30,
    ) -> None:
        if not base_url or not api_key or not model:
            raise RuntimeError("LLM is not configured: base URL, API key, and model are required.")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate_plan(
        self,
        *,
        query: str,
        schema: list[dict[str, Any]],
        recent_messages: list[dict[str, Any]],
        intent: str,
    ) -> dict[str, Any]:
        """Ask the LLM for a constrained JSON planning object."""
        prompt = build_planner_prompt(
            query=query,
            schema=schema,
            recent_messages=recent_messages,
            intent=intent,
        )
        content = self._chat_completion(prompt)
        return _parse_json_object(content)

    def generate_response(
        self,
        *,
        query: str,
        schema: list[dict[str, Any]],
        analysis_plan: list[str],
        tool_result: dict[str, Any],
        chart_url: str | None = None,
        error: str | None = None,
        follow_up_questions: list[str] | None = None,
    ) -> str | dict[str, Any]:
        """Ask the LLM to summarize existing tool output into a user-facing answer."""
        prompt = build_response_prompt(
            query=query,
            schema=schema,
            analysis_plan=analysis_plan,
            tool_result=tool_result,
            chart_url=chart_url,
            error=error,
            follow_up_questions=follow_up_questions,
        )
        return self._chat_completion(prompt)

    def _chat_completion(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a constrained data analysis assistant.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
        }
        request = urllib.request.Request(
            url=f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"LLM request failed: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError("LLM response was not valid JSON.") from exc

        try:
            return str(data["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("LLM response did not contain chat message content.") from exc


def get_llm_client(settings: Any) -> BaseLLMClient:
    """Return a configured LLM client or a NoOp client with a clear reason."""
    if not settings.LLM_ENABLED:
        return NoOpLLMClient("LLM is disabled")

    if settings.LLM_PROVIDER != "openai_compatible":
        return NoOpLLMClient(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")

    missing = [
        name
        for name, value in {
            "LLM_API_KEY": settings.LLM_API_KEY,
            "LLM_MODEL": settings.LLM_MODEL,
            "LLM_BASE_URL": settings.LLM_BASE_URL,
        }.items()
        if not value
    ]
    if missing:
        return NoOpLLMClient("LLM is not configured: missing " + ", ".join(missing))

    return OpenAICompatibleLLMClient(
        base_url=settings.LLM_BASE_URL,
        api_key=settings.LLM_API_KEY,
        model=settings.LLM_MODEL,
        timeout_seconds=settings.LLM_TIMEOUT_SECONDS,
    )


def _parse_json_object(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise RuntimeError("LLM planner response did not contain a JSON object.")
    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise RuntimeError("LLM planner response was not valid JSON.") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError("LLM planner response must be a JSON object.")
    return parsed
