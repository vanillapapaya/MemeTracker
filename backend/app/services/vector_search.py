from uuid import UUID

from app.core.qdrant import qdrant, CLIP_COLLECTION, TEXT_COLLECTION
from app.services.vectorizer import encode_text_clip, encode_text_e5


def hybrid_search(
    query: str,
    limit: int = 20,
    offset: int = 0,
    content_type: str | None = None,
    source: str | None = None,
) -> list[dict]:
    """하이브리드 벡터 검색: CLIP(0.4) + e5-large(0.6) 가중 합산"""
    clip_vector = encode_text_clip(query)
    text_vector = encode_text_e5(query)

    # Qdrant 필터
    filters = _build_filter(content_type, source)

    # CLIP 검색
    clip_results = qdrant.search(
        collection_name=CLIP_COLLECTION,
        query_vector=clip_vector,
        limit=limit + offset + 20,  # 머지를 위해 여유 확보
        query_filter=filters,
    )

    # 텍스트 검색
    text_results = qdrant.search(
        collection_name=TEXT_COLLECTION,
        query_vector=text_vector,
        limit=limit + offset + 20,
        query_filter=filters,
    )

    # 가중 합산
    scores: dict[str, float] = {}
    payloads: dict[str, dict] = {}

    for hit in clip_results:
        image_id = hit.payload.get("image_id", str(hit.id))
        scores[image_id] = 0.4 * hit.score
        payloads[image_id] = hit.payload

    for hit in text_results:
        image_id = hit.payload.get("image_id", str(hit.id))
        scores[image_id] = scores.get(image_id, 0) + 0.6 * hit.score
        if image_id not in payloads:
            payloads[image_id] = hit.payload

    # 정렬 + 페이지네이션
    sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)
    page = sorted_ids[offset : offset + limit]

    return [
        {"image_id": uid, "score": scores[uid], "payload": payloads[uid]}
        for uid in page
    ]


def similar_images(image_id: str, limit: int = 8) -> list[dict]:
    """CLIP 벡터 기반 유사 이미지 검색"""
    # 해당 이미지의 벡터 조회
    points = qdrant.retrieve(collection_name=CLIP_COLLECTION, ids=[image_id], with_vectors=True)
    if not points:
        return []

    vector = points[0].vector
    results = qdrant.search(
        collection_name=CLIP_COLLECTION,
        query_vector=vector,
        limit=limit + 1,  # 자기 자신 제외용
    )
    return [
        {"image_id": hit.payload.get("image_id", str(hit.id)), "score": hit.score, "payload": hit.payload}
        for hit in results
        if hit.payload.get("image_id") != image_id
    ][:limit]


def _build_filter(content_type: str | None, source: str | None):
    """Qdrant 검색 필터 빌드"""
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    conditions = [FieldCondition(key="is_nsfw", match=MatchValue(value=False))]
    if content_type and content_type != "all":
        conditions.append(FieldCondition(key="content_type", match=MatchValue(value=content_type)))
    if source and source != "all":
        conditions.append(FieldCondition(key="source", match=MatchValue(value=source)))

    return Filter(must=conditions) if conditions else None
