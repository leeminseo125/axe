"""ERP System Connector - Reads ERP data without modification."""

from shared_infra.config import get_settings
from axengine.integration_layer.connector_base import ConnectorBase, CanonicalRecord

settings = get_settings()


class ERPConnector(ConnectorBase):
    def __init__(self):
        super().__init__(
            name="erp",
            endpoint=settings.erp_system_endpoint,
            api_key=settings.erp_api_key,
        )

    async def fetch_records(self, resource: str = "orders", **kwargs) -> list[CanonicalRecord]:
        if not self.endpoint:
            return []

        data = await self.read(f"/api/{resource}", params=kwargs)
        if "error" in data:
            return []

        records = data if isinstance(data, list) else data.get("items", data.get("results", []))
        return [
            CanonicalRecord(
                source_system="erp",
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
