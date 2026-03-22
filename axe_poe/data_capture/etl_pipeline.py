"""L1 Data Capture - ETL pipeline for heterogeneous external data sources.

Collects user behavior, product events, CS tickets, and payment data,
normalizes into a canonical event format, and stores for downstream processing.
"""

from datetime import datetime
from uuid import uuid4

import httpx
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from shared_infra.config import get_settings
from shared_infra.data_foundation.models import POEDataEvent

settings = get_settings()
logger = structlog.get_logger()


class EventNormalizer:
    """Transforms raw external data into normalized POE events."""

    @staticmethod
    def normalize(source: str, event_type: str, raw: dict) -> dict:
        """Extract common fields from diverse source formats."""
        normalized = {
            "source": source,
            "event_type": event_type,
            "timestamp": raw.get("timestamp") or raw.get("created_at") or datetime.utcnow().isoformat(),
            "entity_id": raw.get("user_id") or raw.get("customer_id") or raw.get("id"),
            "entity_type": _infer_entity_type(source),
        }

        # Source-specific field extraction
        if source == "analytics":
            normalized["action"] = raw.get("event_name") or raw.get("action")
            normalized["properties"] = raw.get("properties", {})
        elif source == "cs_tickets":
            normalized["subject"] = raw.get("subject") or raw.get("title")
            normalized["priority"] = raw.get("priority", "normal")
            normalized["status"] = raw.get("status", "open")
        elif source == "payments":
            normalized["amount"] = raw.get("amount")
            normalized["currency"] = raw.get("currency", "USD")
            normalized["status"] = raw.get("status")
        elif source == "product_db":
            normalized["product_id"] = raw.get("product_id") or raw.get("id")
            normalized["metrics"] = raw.get("metrics", {})

        return normalized


def _infer_entity_type(source: str) -> str:
    return {
        "analytics": "user",
        "cs_tickets": "customer",
        "payments": "transaction",
        "product_db": "product",
    }.get(source, "unknown")


class DataCaptureService:
    """Orchestrates data capture from all external product sources."""

    def __init__(self):
        self.normalizer = EventNormalizer()
        self.source_configs = {
            "analytics": {
                "endpoint": None,
                "api_key": settings.user_analytics_api_key,
            },
            "cs_tickets": {
                "endpoint": settings.cs_ticket_system_api,
                "api_key": None,
            },
            "payments": {
                "endpoint": settings.payment_gateway_api,
                "api_key": None,
            },
            "product_db": {
                "endpoint": settings.product_db_endpoint,
                "api_key": None,
            },
        }

    async def capture_from_source(
        self, source: str, event_type: str, raw_data: list[dict], db: AsyncSession
    ) -> list[POEDataEvent]:
        """Capture and store normalized events from a source."""
        events = []
        for raw in raw_data:
            normalized = self.normalizer.normalize(source, event_type, raw)
            event = POEDataEvent(
                source=source,
                event_type=event_type,
                raw_payload=raw,
                normalized_payload=normalized,
            )
            db.add(event)
            events.append(event)

        await db.commit()
        for e in events:
            await db.refresh(e)
        return events

    async def pull_from_endpoint(
        self, source: str, event_type: str, path: str, db: AsyncSession
    ) -> list[POEDataEvent]:
        """Pull data from a configured external endpoint and capture it."""
        config = self.source_configs.get(source)
        if not config or not config.get("endpoint"):
            return []

        headers = {}
        if config.get("api_key"):
            headers["Authorization"] = f"Bearer {config['api_key']}"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(f"{config['endpoint']}{path}", headers=headers)
                resp.raise_for_status()
                data = resp.json()
                items = data if isinstance(data, list) else data.get("items", data.get("results", [data]))
                return await self.capture_from_source(source, event_type, items, db)
        except Exception as e:
            logger.error("capture_pull_error", source=source, error=str(e))
            return []

    async def ingest_webhook(
        self, source: str, event_type: str, payload: dict, db: AsyncSession
    ) -> POEDataEvent:
        """Ingest a single event from a webhook push."""
        normalized = self.normalizer.normalize(source, event_type, payload)
        event = POEDataEvent(
            source=source,
            event_type=event_type,
            raw_payload=payload,
            normalized_payload=normalized,
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)
        return event
