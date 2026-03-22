"""Connector Registry - Central access point for all integration connectors."""

from axengine.integration_layer.connector_base import ConnectorBase
from axengine.integration_layer.erp_connector import ERPConnector
from axengine.integration_layer.mes_connector import MESConnector
from axengine.integration_layer.crm_connector import CRMConnector


class ConnectorRegistry:
    """Singleton registry for all integration connectors."""

    _instance = None
    _connectors: dict[str, ConnectorBase] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._connectors = {
                "erp": ERPConnector(),
                "mes": MESConnector(),
                "crm": CRMConnector(),
            }
        return cls._instance

    def get(self, name: str) -> ConnectorBase | None:
        return self._connectors.get(name)

    def list_connectors(self) -> list[str]:
        return list(self._connectors.keys())

    def register(self, name: str, connector: ConnectorBase):
        self._connectors[name] = connector

    async def health_check_all(self) -> dict[str, bool]:
        results = {}
        for name, connector in self._connectors.items():
            try:
                results[name] = await connector.health_check()
            except Exception:
                results[name] = False
        return results

    async def close_all(self):
        for connector in self._connectors.values():
            await connector.close()
