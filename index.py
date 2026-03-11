"""
이미지 인덱서: 폴더 스캔 → VLM 태깅 → CLIP 임베딩 → SQLite 저장

사용법:
    python index.py /path/to/images
    python index.py /path/to/images --db custom.db
    python index.py /path/to/images --reindex  # 기존 인덱스 무시하고 재인덱싱
"""

import argparse
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np
import open_clip
import torch
from PIL import Image
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
DB_DEFAULT = "images.db"

# VLM 프롬프트: 한국어 태그 + 설명 생성
VLM_PROMPT = """이 이미지를 분석해서 다음 형식으로 응답해줘:

태그: (쉼표로 구분된 한국어 태그 5-10개. 캐릭터명, 작품명, 분위기, 상황 등)
설명: (한국어로 1-2문장 설명)

예시:
태그: 고양이, 밈, 웃긴, 놀란 표정, 동물
설명: 놀란 표정을 짓고 있는 고양이 밈 이미지."""


def init_db(db_path: str) -> sqlite3.Connection:
    """SQLite DB 초기화"""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY,
            path TEXT UNIQUE,
            filename TEXT,
            tags TEXT,
            description TEXT,
            clip_embedding BLOB,
            indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def get_indexed_paths(conn: sqlite3.Connection) -> set[str]:
    """이미 인덱싱된 파일 경로 목록"""
    rows = conn.execute("SELECT path FROM images").fetchall()
    return {row[0] for row in rows}


def scan_images(root: str) -> list[Path]:
    """폴더 재귀 스캔하여 이미지 파일 목록 반환"""
    root_path = Path(root)
    if not root_path.exists():
        print(f"오류: 경로가 존재하지 않습니다: {root}")
        sys.exit(1)

    images = []
    for ext in IMAGE_EXTENSIONS:
        images.extend(root_path.rglob(f"*{ext}"))
        images.extend(root_path.rglob(f"*{ext.upper()}"))
    # 중복 제거 (대소문자 확장자)
    seen = set()
    unique = []
    for p in images:
        resolved = str(p.resolve())
        if resolved not in seen:
            seen.add(resolved)
            unique.append(p)
    return sorted(unique)


def load_vlm(device: str):
    """Qwen2.5-VL-7B-Instruct 로드"""
    model_name = "Qwen/Qwen2.5-VL-7B-Instruct"
    print(f"VLM 로딩 중: {model_name}")
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map=device,
    )
    processor = AutoProcessor.from_pretrained(model_name)
    print("VLM 로딩 완료")
    return model, processor


def load_clip(device: str):
    """CLIP ViT-B/32 로드"""
    print("CLIP 로딩 중: ViT-B-32")
    model, _, preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained="laion2b_s34b_b79k"
    )
    model = model.to(device).eval()
    print("CLIP 로딩 완료")
    return model, preprocess


def generate_tags(
    image_path: Path,
    vlm_model,
    vlm_processor,
) -> tuple[str, str]:
    """VLM으로 태그 + 설명 생성"""
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": str(image_path)},
                {"type": "text", "text": VLM_PROMPT},
            ],
        }
    ]
    text = vlm_processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = vlm_processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    ).to(vlm_model.device)

    with torch.no_grad():
        output_ids = vlm_model.generate(**inputs, max_new_tokens=256)
    # 입력 토큰 제외
    generated = output_ids[0][inputs.input_ids.shape[1]:]
    response = vlm_processor.decode(generated, skip_special_tokens=True).strip()

    # 태그/설명 파싱
    tags = ""
    description = ""
    for line in response.split("\n"):
        line = line.strip()
        if line.startswith("태그:"):
            tags = line[len("태그:"):].strip()
        elif line.startswith("설명:"):
            description = line[len("설명:"):].strip()

    # 파싱 실패 시 전체 응답을 설명으로 사용
    if not tags and not description:
        description = response

    return tags, description


def generate_embedding(
    image_path: Path,
    clip_model,
    clip_preprocess,
    device: str,
) -> np.ndarray:
    """CLIP 이미지 임베딩 생성 (512d float32)"""
    image = Image.open(image_path).convert("RGB")
    image_tensor = clip_preprocess(image).unsqueeze(0).to(device)
    with torch.no_grad():
        embedding = clip_model.encode_image(image_tensor)
        embedding = embedding / embedding.norm(dim=-1, keepdim=True)
    return embedding.cpu().numpy().astype(np.float32).flatten()


def main():
    parser = argparse.ArgumentParser(description="이미지 인덱서")
    parser.add_argument("image_dir", help="이미지 폴더 경로")
    parser.add_argument("--db", default=DB_DEFAULT, help=f"SQLite DB 경로 (기본값: {DB_DEFAULT})")
    parser.add_argument("--reindex", action="store_true", help="기존 인덱스 무시하고 재인덱싱")
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"디바이스: {device}")

    # DB 초기화
    conn = init_db(args.db)

    # 이미지 스캔
    all_images = scan_images(args.image_dir)
    print(f"발견된 이미지: {len(all_images)}개")

    if not all_images:
        print("인덱싱할 이미지가 없습니다.")
        return

    # 이미 인덱싱된 파일 필터링
    if args.reindex:
        images = all_images
        print("재인덱싱 모드: 모든 이미지를 다시 처리합니다.")
    else:
        indexed = get_indexed_paths(conn)
        images = [p for p in all_images if str(p.resolve()) not in indexed]
        skipped = len(all_images) - len(images)
        if skipped > 0:
            print(f"이미 인덱싱됨: {skipped}개 스킵")

    if not images:
        print("새로 인덱싱할 이미지가 없습니다.")
        return

    print(f"인덱싱 대상: {len(images)}개")

    # 모델 로드
    vlm_model, vlm_processor = load_vlm(device)
    clip_model, clip_preprocess = load_clip(device)

    # 인덱싱 루프
    success = 0
    errors = 0
    start_time = time.time()

    for i, image_path in enumerate(images, 1):
        try:
            # 진행률
            elapsed = time.time() - start_time
            rate = i / elapsed if elapsed > 0 else 0
            eta = (len(images) - i) / rate if rate > 0 else 0
            print(f"[{i}/{len(images)}] {image_path.name} (ETA: {eta:.0f}s)", end=" ... ")

            # VLM 태깅
            tags, description = generate_tags(image_path, vlm_model, vlm_processor)

            # CLIP 임베딩
            embedding = generate_embedding(image_path, clip_model, clip_preprocess, device)

            # SQLite 저장
            resolved = str(image_path.resolve())
            conn.execute(
                """
                INSERT OR REPLACE INTO images (path, filename, tags, description, clip_embedding)
                VALUES (?, ?, ?, ?, ?)
                """,
                (resolved, image_path.name, tags, description, embedding.tobytes()),
            )
            conn.commit()

            print(f"OK ({tags[:50]}...)" if len(tags) > 50 else f"OK ({tags})")
            success += 1

        except Exception as e:
            print(f"오류: {e}")
            errors += 1
            continue

    elapsed = time.time() - start_time
    print(f"\n완료! 성공: {success}, 오류: {errors}, 소요: {elapsed:.1f}s")
    print(f"DB 저장: {args.db}")
    conn.close()


if __name__ == "__main__":
    main()
