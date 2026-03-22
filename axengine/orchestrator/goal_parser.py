"""Goal Parser - Decomposes business goals into executable task units.

Takes a natural-language or structured goal and breaks it into
atomic, sequenceable steps that the Planner can schedule.
"""

import json
import httpx
from pydantic import BaseModel, Field

from shared_infra.config import get_settings

settings = get_settings()


class ParsedStep(BaseModel):
    index: int
    action: str
    agent: str | None = None
    params: dict = Field(default_factory=dict)
    dependencies: list[int] = Field(default_factory=list)
    estimated_confidence: float = 0.9


class ParsedGoal(BaseModel):
    original_goal: str
    steps: list[ParsedStep]
    requires_human_review: bool = False


# Default decomposition templates for common goal patterns
GOAL_TEMPLATES = {
    "report": [
        ParsedStep(index=0, action="fetch_data", agent="data_connector"),
        ParsedStep(index=1, action="analyze_data", agent="analytics_agent", dependencies=[0]),
        ParsedStep(index=2, action="generate_report", agent="report_agent", dependencies=[1]),
        ParsedStep(index=3, action="distribute_report", agent="notification_agent", dependencies=[2]),
    ],
    "monitor": [
        ParsedStep(index=0, action="collect_metrics", agent="metrics_collector"),
        ParsedStep(index=1, action="evaluate_thresholds", agent="threshold_agent", dependencies=[0]),
        ParsedStep(index=2, action="alert_if_needed", agent="notification_agent", dependencies=[1]),
    ],
    "sync": [
        ParsedStep(index=0, action="read_source", agent="data_connector"),
        ParsedStep(index=1, action="transform_data", agent="etl_agent", dependencies=[0]),
        ParsedStep(index=2, action="write_target", agent="data_connector", dependencies=[1]),
        ParsedStep(index=3, action="verify_sync", agent="validation_agent", dependencies=[2]),
    ],
}


async def parse_goal_with_llm(goal_text: str) -> ParsedGoal:
    """Use LLM to decompose a goal into executable steps."""
    prompt = f"""You are a goal decomposition engine. Break down the following business goal
into a sequence of atomic, executable steps. Each step should have:
- action: a verb_noun action name
- agent: which type of agent should handle it
- params: any parameters needed
- dependencies: indices of steps that must complete first

Goal: {goal_text}

Respond with valid JSON matching this structure:
{{"steps": [{{"index": 0, "action": "...", "agent": "...", "params": {{}}, "dependencies": []}}]}}"""

    # Try local LLM first (Ollama), fall back to OpenAI
    steps = await _call_local_llm(prompt)
    if steps is None and settings.openai_api_key:
        steps = await _call_openai(prompt)

    if steps:
        return ParsedGoal(original_goal=goal_text, steps=steps)

    # Fallback: pattern matching on keywords
    return _template_fallback(goal_text)


async def _call_local_llm(prompt: str) -> list[ParsedStep] | None:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                settings.local_llm_endpoint,
                json={"model": "llama3", "prompt": prompt, "stream": False},
            )
            if resp.status_code == 200:
                text = resp.json().get("response", "")
                return _extract_steps(text)
    except Exception:
        return None


async def _call_openai(prompt: str) -> list[ParsedStep] | None:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                },
            )
            if resp.status_code == 200:
                text = resp.json()["choices"][0]["message"]["content"]
                return _extract_steps(text)
    except Exception:
        return None


def _extract_steps(text: str) -> list[ParsedStep] | None:
    try:
        # Find JSON in the response
        start = text.index("{")
        end = text.rindex("}") + 1
        data = json.loads(text[start:end])
        return [ParsedStep(**s) for s in data.get("steps", [])]
    except (ValueError, json.JSONDecodeError, KeyError):
        return None


def _template_fallback(goal_text: str) -> ParsedGoal:
    lower = goal_text.lower()
    for keyword, template in GOAL_TEMPLATES.items():
        if keyword in lower:
            return ParsedGoal(original_goal=goal_text, steps=template)

    # Generic two-step fallback
    return ParsedGoal(
        original_goal=goal_text,
        steps=[
            ParsedStep(index=0, action="analyze_request", agent="general_agent"),
            ParsedStep(index=1, action="execute_action", agent="general_agent", dependencies=[0]),
        ],
        requires_human_review=True,
    )
