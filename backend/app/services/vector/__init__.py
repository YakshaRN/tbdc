# Vector services module
from app.services.vector.embedding_service import embedding_service
from app.services.vector.marketing_vector_store import marketing_vector_store

__all__ = ["embedding_service", "marketing_vector_store"]
