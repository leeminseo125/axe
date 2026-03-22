"""Qdrant vector store client for RAG and knowledge memory."""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from shared_infra.config import get_settings

settings = get_settings()

qdrant_client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)

COLLECTIONS = {
    "axengine_knowledge": {"size": 1536, "distance": Distance.COSINE},
    "poe_playbook": {"size": 1536, "distance": Distance.COSINE},
    "policy_rules": {"size": 1536, "distance": Distance.COSINE},
}


def init_vector_collections():
    """Create vector collections if they don't exist."""
    existing = {c.name for c in qdrant_client.get_collections().collections}
    for name, params in COLLECTIONS.items():
        if name not in existing:
            qdrant_client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=params["size"], distance=params["distance"]),
            )


def upsert_vectors(collection: str, points: list[PointStruct]):
    qdrant_client.upsert(collection_name=collection, points=points)


def search_vectors(collection: str, query_vector: list[float], limit: int = 5):
    return qdrant_client.query_points(
        collection_name=collection,
        query=query_vector,
        limit=limit,
    )
