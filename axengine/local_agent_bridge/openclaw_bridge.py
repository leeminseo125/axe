"""OpenClaw Bridge - Non-destructive UI automation controller.

Provides a connector interface for OpenClaw-based UI automation,
enabling AI to interact with legacy systems that lack APIs
through screen-level automation scripts.
"""

import httpx
import structlog

logger = structlog.get_logger()


class OpenClawBridge:
    """Bridge to an OpenClaw automation environment.

    OpenClaw handles UI-level interactions with legacy systems.
    This bridge sends high-level commands and reads results
    without directly modifying the target systems.
    """

    def __init__(self, endpoint: str = "http://localhost:9000"):
        self.endpoint = endpoint

    async def execute_script(self, script_name: str, params: dict | None = None) -> dict:
        """Execute a named automation script in the OpenClaw environment."""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{self.endpoint}/scripts/execute",
                    json={"script": script_name, "params": params or {}},
                )
                if resp.status_code == 200:
                    return resp.json()
                return {"error": f"OpenClaw returned {resp.status_code}", "body": resp.text}
        except Exception as e:
            logger.error("openclaw_error", script=script_name, error=str(e))
            return {"error": str(e)}

    async def capture_screen(self, target: str) -> dict:
        """Capture screen state from a legacy application via OpenClaw."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"{self.endpoint}/capture",
                    params={"target": target},
                )
                if resp.status_code == 200:
                    return resp.json()
                return {"error": f"Capture failed: {resp.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def list_scripts(self) -> list[str]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.endpoint}/scripts")
                if resp.status_code == 200:
                    return resp.json().get("scripts", [])
        except Exception:
            pass
        return []

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.endpoint}/health")
                return resp.status_code == 200
        except Exception:
            return False
