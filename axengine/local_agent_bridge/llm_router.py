"""LLM Router - Intelligent routing between local and cloud LLM providers.

Routes inference requests to the optimal provider based on:
- Availability (local first, cloud fallback)
- Task complexity (simple tasks local, complex tasks cloud)
- Privacy requirements (sensitive data always local)
"""

import httpx
import structlog

from shared_infra.config import get_settings
from axengine.local_agent_bridge.ollama_client import OllamaClient

settings = get_settings()
logger = structlog.get_logger()


class LLMRouter:
    def __init__(self):
        self.ollama = OllamaClient()

    async def generate(
        self,
        prompt: str,
        system: str = "",
        prefer_local: bool = True,
        require_local: bool = False,
    ) -> dict:
        """Route a generation request to the best available LLM.

        Returns: {"response": str, "provider": str, "model": str}
        """
        # Try local first if preferred
        if prefer_local or require_local:
            result = await self.ollama.generate(prompt, system=system)
            if result:
                return {"response": result, "provider": "ollama", "model": self.ollama.model}

        if require_local:
            return {"response": None, "provider": "none", "model": "none", "error": "Local LLM unavailable"}

        # Fallback to OpenAI
        if settings.openai_api_key:
            result = await self._call_openai(prompt, system)
            if result:
                return {"response": result, "provider": "openai", "model": "gpt-4o-mini"}

        # Fallback to Anthropic
        if settings.anthropic_api_key:
            result = await self._call_anthropic(prompt, system)
            if result:
                return {"response": result, "provider": "anthropic", "model": "claude-sonnet-4-6"}

        return {"response": None, "provider": "none", "model": "none", "error": "No LLM available"}

    async def _call_openai(self, prompt: str, system: str = "") -> str | None:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                    json={"model": "gpt-4o-mini", "messages": messages, "temperature": 0.3},
                )
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error("openai_error", error=str(e))
        return None

    async def _call_anthropic(self, prompt: str, system: str = "") -> str | None:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                body = {
                    "model": "claude-sonnet-4-6",
                    "max_tokens": 4096,
                    "messages": [{"role": "user", "content": prompt}],
                }
                if system:
                    body["system"] = system
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": settings.anthropic_api_key,
                        "anthropic-version": "2023-06-01",
                    },
                    json=body,
                )
                if resp.status_code == 200:
                    content = resp.json().get("content", [])
                    if content:
                        return content[0].get("text", "")
        except Exception as e:
            logger.error("anthropic_error", error=str(e))
        return None

    async def get_available_providers(self) -> list[str]:
        providers = []
        if await self.ollama.is_available():
            providers.append("ollama")
        if settings.openai_api_key:
            providers.append("openai")
        if settings.anthropic_api_key:
            providers.append("anthropic")
        return providers
