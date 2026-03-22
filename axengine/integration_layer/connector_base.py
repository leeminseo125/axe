"""Anti-Corruption Layer - Base connector for legacy system integration.

All connectors inherit from this base and translate external data
into the AXEworks canonical data model without modifying the source.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from pydantic import BaseModel, Field
import httpx
import structlog

logger = structlog.get_logger()


class CanonicalRecord(BaseModel):
    """Standardized record format for all data flowing into AXEngine."""
    source_system: str
    source_id: str
    record_type: str
    data: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict)


class ConnectorBase(ABC):
    """Base class for all legacy system connectors.

    Implements the Anti-Corruption Layer pattern: reads data from
    external systems and translates to canonical format.
    The source system is NEVER modified.
    """

    def __init__(self, name: str, endpoint: str, api_key: str = ""):
        self.name = name
        self.endpoint = endpoint
        self.api_key = api_key
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._client = httpx.AsyncClient(
                base_url=self.endpoint,
                headers=headers,
                timeout=15.0,
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def read(self, path: str, params: dict | None = None) -> dict:
        """Read data from the external system (GET)."""
        client = await self._get_client()
        try:
            resp = await client.get(path, params=params)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.error("connector_read_error", connector=self.name, path=path, error=str(e))
            return {"error": str(e)}

    @abstractmethod
    async def fetch_records(self, **kwargs) -> list[CanonicalRecord]:
        """Fetch and translate records to canonical format."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the external system is reachable."""
        ...
