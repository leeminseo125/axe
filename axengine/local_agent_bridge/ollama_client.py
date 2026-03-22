"""Ollama Client - Local LLM inference bridge.

Connects to a locally hosted Ollama instance for private,
low-latency AI inference without external API dependency.
"""

import httpx
import structlog

from shared_infra.config import get_settings

settings = get_settings()
logger = structlog.get_logger()


class OllamaClient:
    def __init__(self, endpoint: str | None = None, model: str = "llama3"):
        self.endpoint = endpoint or settings.local_llm_endpoint
        self.model = model
        # Derive base URL by stripping the path
        if "/api/" in self.endpoint:
            self.base_url = self.endpoint.rsplit("/api/", 1)[0]
        else:
            self.base_url = self.endpoint

    async def generate(self, prompt: str, system: str = "", temperature: float = 0.3) -> str | None:
        """Generate a completion from the local LLM."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(f"{self.base_url}/api/generate", json=payload)
                if resp.status_code == 200:
                    return resp.json().get("response")
                logger.warning("ollama_non_200", status=resp.status_code)
        except Exception as e:
            logger.error("ollama_error", error=str(e))
        return None

    async def chat(self, messages: list[dict], temperature: float = 0.3) -> str | None:
        """Chat completion via local Ollama model."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(f"{self.base_url}/api/chat", json=payload)
                if resp.status_code == 200:
                    return resp.json().get("message", {}).get("content")
        except Exception as e:
            logger.error("ollama_chat_error", error=str(e))
        return None

    async def list_models(self) -> list[str]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                if resp.status_code == 200:
                    models = resp.json().get("models", [])
                    return [m.get("name", "") for m in models]
        except Exception:
            pass
        return []

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False
