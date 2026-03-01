import logging

logger = logging.getLogger(__name__)

_clip_model = None
_clip_preprocess = None
_clip_tokenizer = None
_text_model = None


def load_clip():
    """CLIP ViT-B/32 모델 로딩 (lazy)"""
    global _clip_model, _clip_preprocess, _clip_tokenizer
    if _clip_model is not None:
        return _clip_model, _clip_preprocess, _clip_tokenizer

    import open_clip

    model, preprocess_train, preprocess_val = open_clip.create_model_and_transforms("ViT-B-32", pretrained="openai")
    tokenizer = open_clip.get_tokenizer("ViT-B-32")
    model.eval()
    _clip_model = model
    _clip_preprocess = preprocess_val
    _clip_tokenizer = tokenizer
    logger.info("CLIP ViT-B/32 loaded")
    return model, preprocess_val, tokenizer


def load_text_model():
    """multilingual-e5-large 모델 로딩 (lazy)"""
    global _text_model
    if _text_model is not None:
        return _text_model

    from sentence_transformers import SentenceTransformer

    _text_model = SentenceTransformer("intfloat/multilingual-e5-large")
    logger.info("multilingual-e5-large loaded")
    return _text_model


def encode_text_clip(text: str) -> list[float]:
    """CLIP 텍스트 인코딩 → 512d 벡터"""
    import torch

    model, _, tokenizer = load_clip()
    tokens = tokenizer([text])
    with torch.no_grad():
        text_features = model.encode_text(tokens)
        text_features /= text_features.norm(dim=-1, keepdim=True)
    return text_features[0].tolist()


def encode_image_clip(image) -> list[float]:
    """CLIP 이미지 인코딩 → 512d 벡터"""
    import torch

    model, preprocess, _ = load_clip()
    image_tensor = preprocess(image).unsqueeze(0)
    with torch.no_grad():
        image_features = model.encode_image(image_tensor)
        image_features /= image_features.norm(dim=-1, keepdim=True)
    return image_features[0].tolist()


def encode_text_e5(text: str) -> list[float]:
    """e5-large 텍스트 인코딩 → 1024d 벡터"""
    model = load_text_model()
    # e5 모델은 "query: " 프리픽스 권장
    embedding = model.encode(f"query: {text}", normalize_embeddings=True)
    return embedding.tolist()
