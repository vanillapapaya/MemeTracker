"""
MemeTracker 웹 서버: 검색 API + 이미지 서빙

사용법:
    python app.py --images /path/to/images
    python app.py --images /path/to/images --db custom.db --port 8000
"""

import argparse
import sqlite3
import urllib.parse
from pathlib import Path

import numpy as np
import open_clip
import torch
import uvicorn
from fastapi import FastAPI, Query, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

DB_DEFAULT = "images.db"


def create_app(db_path: str, images_root: str) -> FastAPI:
    app = FastAPI(title="MemeTracker")
    templates = Jinja2Templates(directory="templates")

    # CLIP 텍스트 인코더 로드
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"디바이스: {device}")
    print("CLIP 로딩 중...")
    clip_model, _, _ = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained="laion2b_s34b_b79k"
    )
    clip_model = clip_model.to(device).eval()
    tokenizer = open_clip.get_tokenizer("ViT-B-32")
    print("CLIP 로딩 완료")

    images_root_resolved = str(Path(images_root).resolve())

    def get_db() -> sqlite3.Connection:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def text_to_embedding(text: str) -> np.ndarray:
        """텍스트 → CLIP 임베딩 (512d)"""
        tokens = tokenizer([text]).to(device)
        with torch.no_grad():
            emb = clip_model.encode_text(tokens)
            emb = emb / emb.norm(dim=-1, keepdim=True)
        return emb.cpu().numpy().astype(np.float32).flatten()

    @app.get("/", response_class=HTMLResponse)
    async def search_page(request: Request):
        """검색 UI 페이지"""
        conn = get_db()
        total = conn.execute("SELECT COUNT(*) FROM images").fetchone()[0]
        conn.close()
        return templates.TemplateResponse("index.html", {"request": request, "total": total})

    @app.get("/api/search")
    async def search(
        q: str = Query(..., min_length=1, description="검색어"),
        limit: int = Query(40, ge=1, le=200, description="결과 수"),
    ):
        """CLIP 텍스트 임베딩 → 코사인 유사도 검색"""
        query_emb = text_to_embedding(q)

        conn = get_db()
        rows = conn.execute(
            "SELECT id, path, filename, tags, description, clip_embedding FROM images"
        ).fetchall()
        conn.close()

        if not rows:
            return {"results": [], "total": 0}

        # 코사인 유사도 계산
        results = []
        for row in rows:
            emb = np.frombuffer(row["clip_embedding"], dtype=np.float32)
            score = float(np.dot(query_emb, emb))
            results.append({
                "id": row["id"],
                "filename": row["filename"],
                "tags": row["tags"],
                "description": row["description"],
                "score": round(score, 4),
                "image_url": f"/images/{urllib.parse.quote(row['path'])}",
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        results = results[:limit]

        return {"results": results, "total": len(rows), "query": q}

    @app.get("/api/browse")
    async def browse(
        offset: int = Query(0, ge=0),
        limit: int = Query(40, ge=1, le=200),
    ):
        """전체 이미지 브라우즈 (최신순)"""
        conn = get_db()
        rows = conn.execute(
            "SELECT id, path, filename, tags, description FROM images ORDER BY indexed_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        total = conn.execute("SELECT COUNT(*) FROM images").fetchone()[0]
        conn.close()

        results = [
            {
                "id": row["id"],
                "filename": row["filename"],
                "tags": row["tags"],
                "description": row["description"],
                "image_url": f"/images/{urllib.parse.quote(row['path'])}",
            }
            for row in rows
        ]

        return {"results": results, "total": total, "offset": offset}

    @app.get("/images/{file_path:path}")
    async def serve_image(file_path: str):
        """이미지 파일 서빙 (보안: images_root 내 파일만 허용)"""
        decoded = urllib.parse.unquote(file_path)
        resolved = str(Path(decoded).resolve())

        # 경로 탐색 공격 방지
        if not resolved.startswith(images_root_resolved):
            return {"error": "접근 불가"}

        path = Path(resolved)
        if not path.exists():
            return {"error": "파일 없음"}

        # MIME 타입 추론
        suffix = path.suffix.lower()
        media_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        media_type = media_types.get(suffix, "application/octet-stream")
        return FileResponse(resolved, media_type=media_type)

    return app


def main():
    parser = argparse.ArgumentParser(description="MemeTracker 웹 서버")
    parser.add_argument("--images", required=True, help="이미지 폴더 경로")
    parser.add_argument("--db", default=DB_DEFAULT, help=f"SQLite DB 경로 (기본값: {DB_DEFAULT})")
    parser.add_argument("--host", default="0.0.0.0", help="호스트 (기본값: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="포트 (기본값: 8000)")
    args = parser.parse_args()

    if not Path(args.db).exists():
        print(f"오류: DB 파일이 없습니다: {args.db}")
        print("먼저 python index.py로 인덱싱하세요.")
        return

    app = create_app(args.db, args.images)
    print(f"\n서버 시작: http://{args.host}:{args.port}")
    print(f"DB: {args.db}")
    print(f"이미지 폴더: {args.images}")
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
