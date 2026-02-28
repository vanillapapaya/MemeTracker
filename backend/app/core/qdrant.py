from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from app.config import settings

qdrant = QdrantClient(url=settings.qdrant_url)

CLIP_COLLECTION = "clip_vectors"
TEXT_COLLECTION = "text_vectors"
CLIP_DIM = 512
TEXT_DIM = 1024


def init_collections():
    """Qdrant 컬렉션 초기화 (없으면 생성)"""
    for name, dim in [(CLIP_COLLECTION, CLIP_DIM), (TEXT_COLLECTION, TEXT_DIM)]:
        if not qdrant.collection_exists(name):
            qdrant.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )
