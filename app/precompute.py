"""
YouTube 데이터 수집 + TF-IDF 사전 계산 스크립트
=================================================
실행: python -m app.precompute (프로젝트 루트에서)
또는: python app/precompute.py

수행 작업:
1. YouTube Data API v3로 한국 인기 영상 카테고리별 50개씩 수집
2. data/youtube_top200_data.csv 저장
3. 카테고리별 TF-IDF 벡터 → data/precomputed/tfidf_{category}.npy + vectorizer_{category}.pkl
4. 카테고리별 통계치 → data/precomputed/category_stats.json
5. 인기 제목 패턴 → data/precomputed/top_titles.json
"""

import os
import json
import pickle
import time
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from dotenv import load_dotenv

# ============================================================
# 설정
# ============================================================
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("precompute")

# 프로젝트 루트 기준 경로 (app/precompute.py → 상위 = 프로젝트 루트)
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PRECOMPUTED_DIR = DATA_DIR / "precomputed"
CSV_PATH = DATA_DIR / "youtube_top200_data.csv"

DATA_DIR.mkdir(parents=True, exist_ok=True)
PRECOMPUTED_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(PROJECT_ROOT / ".env")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")

# ============================================================
# 수집 대상 카테고리 (YouTube 카테고리 ID → 이름)
# ============================================================
CATEGORIES = {
    "10": "Music",
    "20": "Gaming",
    "22": "People_and_Blogs",
    "23": "Comedy",
    "24": "Entertainment",
    "25": "News_and_Politics",
    "26": "Howto_and_Style",
    "27": "Education",
    "28": "Science_and_Technology",
    "17": "Sports",
    "15": "Pets_and_Animals",
    "19": "Travel_and_Events",
    "2":  "Autos_and_Vehicles",
    "1":  "Film_and_Animation",
}

MAX_PER_CATEGORY = 50  # 카테고리당 최대 수집 영상 수
REGION_CODE = "KR"     # 한국 인기 영상 기준
YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"


# ============================================================
# 1. YouTube Data API v3 수집
# ============================================================
def fetch_popular_videos(category_id: str, category_name: str, max_results: int = 50) -> list[dict]:
    """
    YouTube mostPopular 차트에서 카테고리별 인기 영상 수집
    한 페이지당 최대 50개, 필요 시 pageToken으로 이어서 수집
    """
    if not YOUTUBE_API_KEY or YOUTUBE_API_KEY == "여기에키입력":
        logger.warning("YOUTUBE_API_KEY 미설정 — 더미 데이터 반환")
        return _dummy_videos(category_name, max_results)

    videos = []
    page_token = None

    while len(videos) < max_results:
        params = {
            "part": "snippet,statistics,contentDetails",
            "chart": "mostPopular",
            "regionCode": REGION_CODE,
            "videoCategoryId": category_id,
            "maxResults": min(50, max_results - len(videos)),
            "key": YOUTUBE_API_KEY,
        }
        if page_token:
            params["pageToken"] = page_token

        try:
            resp = requests.get(f"{YOUTUBE_API_BASE}/videos", params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            logger.error(f"API 요청 실패 ({category_name}): {e}")
            break

        items = data.get("items", [])
        if not items:
            break

        for item in items:
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            content = item.get("contentDetails", {})

            videos.append({
                "video_id": item.get("id", ""),
                "title": snippet.get("title", ""),
                "description": snippet.get("description", "")[:500],
                "channel_title": snippet.get("channelTitle", ""),
                "category_id": category_id,
                "category_name": category_name,
                "tags": "|".join(snippet.get("tags", [])),
                "published_at": snippet.get("publishedAt", ""),
                "view_count": int(stats.get("viewCount", 0)),
                "like_count": int(stats.get("likeCount", 0)),
                "comment_count": int(stats.get("commentCount", 0)),
                "duration": content.get("duration", ""),
                "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
            })

        page_token = data.get("nextPageToken")
        if not page_token:
            break

        time.sleep(0.1)  # API 레이트 리밋 방지

    logger.info(f"  [{category_name}] {len(videos)}개 수집 완료")
    return videos


def _dummy_videos(category_name: str, count: int) -> list[dict]:
    """API 키 없을 때 사용할 더미 데이터 (구조 테스트용)"""
    return [
        {
            "video_id": f"dummy_{i}",
            "title": f"[더미] {category_name} 인기 영상 {i+1}",
            "description": f"{category_name} 카테고리 더미 설명",
            "channel_title": "더미 채널",
            "category_id": "0",
            "category_name": category_name,
            "tags": f"{category_name}|인기|한국",
            "published_at": "2024-01-01T00:00:00Z",
            "view_count": 100000 * (count - i),
            "like_count": 5000 * (count - i),
            "comment_count": 500 * (count - i),
            "duration": "PT10M",
            "thumbnail_url": "",
        }
        for i in range(count)
    ]


# ============================================================
# 2. 전체 카테고리 수집 → CSV 저장
# ============================================================
def collect_all_categories() -> pd.DataFrame:
    """모든 카테고리 수집 후 DataFrame 반환"""
    logger.info("=" * 60)
    logger.info(f"YouTube 인기 영상 수집 시작 (지역: {REGION_CODE})")
    logger.info("=" * 60)

    all_videos = []
    for cat_id, cat_name in CATEGORIES.items():
        logger.info(f"수집 중: {cat_name} (ID: {cat_id})")
        videos = fetch_popular_videos(cat_id, cat_name, MAX_PER_CATEGORY)
        all_videos.extend(videos)
        time.sleep(0.2)  # 카테고리 간 딜레이

    df = pd.DataFrame(all_videos)
    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
    logger.info(f"\n총 {len(df)}개 영상 → {CSV_PATH}")
    return df


# ============================================================
# 3. TF-IDF 사전 계산
# ============================================================
def compute_tfidf(df: pd.DataFrame):
    """카테고리별 TF-IDF 벡터 계산 후 저장"""
    logger.info("\nTF-IDF 사전 계산 중...")

    # 제목 + 태그를 합쳐서 텍스트 피처 생성
    df["text_feature"] = df["title"] + " " + df["tags"].fillna("").str.replace("|", " ")

    for category in df["category_name"].unique():
        cat_df = df[df["category_name"] == category].copy()
        texts = cat_df["text_feature"].fillna("").tolist()

        if len(texts) < 2:
            logger.warning(f"  [{category}] 영상 수 부족 ({len(texts)}개) — 스킵")
            continue

        vectorizer = TfidfVectorizer(max_features=500, ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform(texts)

        # .npy 저장
        npy_path = PRECOMPUTED_DIR / f"tfidf_{category}.npy"
        np.save(npy_path, tfidf_matrix.toarray())

        # vectorizer pickle 저장
        pkl_path = PRECOMPUTED_DIR / f"vectorizer_{category}.pkl"
        with open(pkl_path, "wb") as f:
            pickle.dump(vectorizer, f)

        logger.info(f"  [{category}] TF-IDF {tfidf_matrix.shape} → 저장 완료")


# ============================================================
# 4. 카테고리 통계 계산
# ============================================================
def compute_stats(df: pd.DataFrame):
    """카테고리별 조회수/좋아요 통계 저장"""
    logger.info("\n카테고리 통계 계산 중...")

    stats = {}
    for category in df["category_name"].unique():
        cat_df = df[df["category_name"] == category]
        stats[category] = {
            "avg_views": int(cat_df["view_count"].mean()),
            "median_views": int(cat_df["view_count"].median()),
            "std_views": int(cat_df["view_count"].std()),
            "avg_likes": int(cat_df["like_count"].mean()),
            "video_count": len(cat_df),
        }

    out_path = PRECOMPUTED_DIR / "category_stats.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    logger.info(f"  {len(stats)}개 카테고리 통계 → {out_path}")


# ============================================================
# 5. 인기 제목 패턴 추출
# ============================================================
def compute_top_titles(df: pd.DataFrame):
    """
    카테고리별 상위 조회수 영상 제목 수집 → top_titles.json
    GPT 프롬프트에서 '인기 제목 패턴' 참고 데이터로 활용
    """
    logger.info("\n인기 제목 패턴 추출 중...")

    top_titles = {}
    for category in df["category_name"].unique():
        cat_df = df[df["category_name"] == category].copy()
        # 조회수 기준 상위 20개 제목
        top = cat_df.nlargest(20, "view_count")["title"].tolist()
        top_titles[category] = top

    out_path = PRECOMPUTED_DIR / "top_titles.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(top_titles, f, ensure_ascii=False, indent=2)

    logger.info(f"  {len(top_titles)}개 카테고리 제목 패턴 → {out_path}")


# ============================================================
# 메인 실행
# ============================================================
def main():
    start = time.time()

    # 1. 수집
    df = collect_all_categories()

    # 2~4. 사전 계산 (순차 처리)
    compute_tfidf(df)
    compute_stats(df)
    compute_top_titles(df)

    elapsed = time.time() - start
    logger.info(f"\n{'='*60}")
    logger.info(f"사전 계산 완료! 총 소요 시간: {elapsed:.1f}초")
    logger.info(f"저장 위치: {PRECOMPUTED_DIR}")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    main()
