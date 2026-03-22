"""CRM System Connector - Reads customer relationship data without modification."""

from shared_infra.config import get_settings
from axengine.integration_layer.connector_base import ConnectorBase, CanonicalRecord

settings = get_settings()


class CRMConnector(ConnectorBase):
    def __init__(self):
        super().__init__(
            name="crm",
            endpoint=settings.crm_system_endpoint,
            api_key=settings.crm_api_key,
        )

    async def fetch_records(self, resource: str = "contacts", **kwargs) -> list[CanonicalRecord]:
        if not self.endpoint:
            return []

        data = await self.read(f"/api/{resource}", params=kwargs)
        if "error" in data:
            return []

        records = data if isinstance(data, list) else data.get("items", data.get("results", []))
        return [
            CanonicalRecord(
                source_system="crm",
                source_id=str(r.get("id", "")),
                record_type=resource,
                data=r,
                metadata={"resource": resource},
            )
            for r in records
        ]

    async def health_check(self) -> bool:
        if not self.endpoint:
            return False
        result = await self.read("/health")
        return "error" not in result
