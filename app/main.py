"""
Think:it Pro — FastAPI 백엔드 메인 서버 (경량화 버전)
===========================================
전략:
1. Lifespan 이벤트로 사전계산 데이터(TF-IDF, 통계치)를 서버 시작 시 1회 로드
2. Whisper/GPT-4o/DALL-E 3은 OpenAI API로 위임 (GPU 불필요)
3. BackgroundTasks로 비동기 처리 (즉시 job_id 반환 → 백그라운드 분석)
4. Coverage/Novelty 지표로 편향성 보정
5. CLIP/PyTorch 제거 — Oracle Free Tier 1GB RAM 환경 최적화
"""

import os
import json
import uuid
import time
import asyncio
import logging
import smtplib
import subprocess
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import numpy as np
import pandas as pd
import pickle
import cv2
import requests as http_requests
from sklearn.metrics.pairwise import cosine_similarity

from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from openai import OpenAI
from dotenv import load_dotenv

# ============================================================
# 로깅 설정
# ============================================================
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("thinkit")

# ============================================================
# 환경변수
# ============================================================
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DATA_DIR       = PROJECT_ROOT / "data"
PRECOMPUTED_DIR = DATA_DIR / "precomputed"
UPLOADS_DIR    = DATA_DIR / "uploads"
OUTPUTS_DIR    = DATA_DIR / "outputs"

for d in [DATA_DIR, PRECOMPUTED_DIR, UPLOADS_DIR, OUTPUTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

WHISPER_MAX_MB = 25  # Whisper API 파일 크기 제한

# ============================================================
# 전역 저장소
# ============================================================
PRECOMPUTED = {}  # TF-IDF 벡터, 통계치, 제목 패턴
JOBS = {}         # 분석 작업 상태 (job_id → 결과)

# ============================================================
# 카테고리 매핑
# ============================================================
CATEGORY_MAP = {
    "Film_and_Animation": "Film & Animation",
    "Autos_and_Vehicles": "Autos & Vehicles",
    "Music": "Music",
    "Pets_and_Animals": "Pets & Animals",
    "Sports": "Sports",
    "Travel_and_Events": "Travel & Events",
    "Gaming": "Gaming",
    "People_and_Blogs": "People & Blogs",
    "Comedy": "Comedy",
    "Entertainment": "Entertainment",
    "News_and_Politics": "News & Politics",
    "Howto_and_Style": "Howto & Style",
    "Education": "Education",
    "Science_and_Technology": "Science & Technology",
}


# ============================================================
# 1. LIFESPAN — 서버 시작/종료 시 데이터 로드/해제
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 시작 시 사전계산 데이터를 메모리에 로드"""
    logger.info("=" * 60)
    logger.info("서버 시작 — 사전계산 데이터 로딩 중...")
    logger.info("=" * 60)

    start = time.time()

    # TF-IDF 벡터 로드
    PRECOMPUTED["tfidf"] = {}
    PRECOMPUTED["vectorizer"] = {}
    for f in PRECOMPUTED_DIR.glob("tfidf_*.npy"):
        category = f.stem.replace("tfidf_", "")
        PRECOMPUTED["tfidf"][category] = np.load(f)
        pkl_path = PRECOMPUTED_DIR / f"vectorizer_{category}.pkl"
        if pkl_path.exists():
            with open(pkl_path, "rb") as pf:
                PRECOMPUTED["vectorizer"][category] = pickle.load(pf)
    logger.info(f"  TF-IDF 벡터: {len(PRECOMPUTED['tfidf'])}개 카테고리")

    # 카테고리 통계
    stats_path = PRECOMPUTED_DIR / "category_stats.json"
    if stats_path.exists():
        with open(stats_path, "r", encoding="utf-8") as f:
            PRECOMPUTED["stats"] = json.load(f)
        logger.info(f"  카테고리 통계: {len(PRECOMPUTED['stats'])}개 카테고리")

    # 인기 제목 패턴
    titles_path = PRECOMPUTED_DIR / "top_titles.json"
    if titles_path.exists():
        with open(titles_path, "r", encoding="utf-8") as f:
            PRECOMPUTED["top_titles"] = json.load(f)
        logger.info(f"  제목 패턴: {len(PRECOMPUTED['top_titles'])}개 카테고리")

    # YouTube 메타데이터
    csv_path = DATA_DIR / "youtube_top200_data.csv"
    if csv_path.exists():
        PRECOMPUTED["df"] = pd.read_csv(csv_path)
        logger.info(f"  YouTube 데이터: {len(PRECOMPUTED['df'])}개 영상")

    elapsed = time.time() - start
    logger.info(f"로딩 완료 ({elapsed:.1f}초)")
    logger.info("=" * 60)

    yield  # 서버 실행

    logger.info("서버 종료 — 리소스 해제")
    PRECOMPUTED.clear()


# ============================================================
# 2. FastAPI 앱 생성
# ============================================================
app = FastAPI(
    title="Think:it Pro API",
    description="멀티모달 AI 기반 유튜브 컨설팅 백엔드",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# /outputs 마운트는 반드시 / 마운트보다 먼저 등록
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")

# OpenAI 클라이언트
client = OpenAI(api_key=OPENAI_API_KEY)


# ============================================================
# 3. 파이프라인 모듈
# ============================================================

# --- 3-1. 프레임 추출 (최대 3장, 640px 리사이즈) ---
def extract_key_frames(video_path: str, max_frames: int = 3) -> list[str]:
    """
    OpenCV로 1fps 간격 프레임 추출 — 최대 3장, 640px 리사이즈로 메모리 절약
    - fps를 읽어 매 1초마다 1장 추출 (1fps)
    - max_frames(3)장까지만 저장
    """
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps          = cap.get(cv2.CAP_PROP_FPS) or 30.0  # fps 읽기 실패 시 30 기본값
    saved_paths  = []

    if total_frames <= 0 or fps <= 0:
        cap.release()
        return saved_paths

    # 1fps 간격으로 추출할 프레임 인덱스 생성, max_frames 초과 시 앞쪽 max_frames개만 사용
    step = int(fps)  # 1초당 프레임 수
    frame_indices = list(range(0, total_frames, step))[:max_frames]

    for i, idx in enumerate(frame_indices):
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            continue

        # 640px 리사이즈 (메모리 절약)
        h, w = frame.shape[:2]
        if w > 640:
            scale = 640 / w
            frame = cv2.resize(frame, (640, int(h * scale)), interpolation=cv2.INTER_AREA)

        path = str(OUTPUTS_DIR / f"frame_{uuid.uuid4().hex[:8]}_{i}.jpg")
        cv2.imwrite(path, frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        saved_paths.append(path)

    cap.release()
    logger.info(f"  프레임 추출: {len(saved_paths)}장 (영상 fps={fps:.1f}, step={step})")
    return saved_paths


# --- 3-2. 오디오 추출 (ffmpeg subprocess) ---
def extract_audio(video_path: str) -> str:
    """ffmpeg subprocess로 오디오 추출 — MoviePy 로드 오버헤드 없이 빠른 추출"""
    audio_path = str(Path(video_path).with_suffix(".mp3"))
    result = subprocess.run(
        ["ffmpeg", "-i", video_path, "-vn", "-acodec", "libmp3lame", "-q:a", "4", "-y", audio_path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error(f"오디오 추출 실패: {result.stderr[-300:]}")
        return ""
    logger.info(f"  오디오 추출 완료: {Path(audio_path).name}")
    return audio_path


# --- 3-3. Whisper API 대본 추출 ---
def transcribe_audio(audio_path: str) -> dict:
    """
    OpenAI Whisper API로 대본 추출
    - 25MB 초과 시 ffmpeg로 16kHz/mono/32kbps 압축 후 전송
    - 전송 완료 후 임시 파일 즉시 삭제
    """
    if not audio_path or not os.path.exists(audio_path):
        return {"text": "", "wpm": 0}

    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    send_path    = audio_path  # 실제로 Whisper에 전송할 경로
    compressed   = False

    if file_size_mb > WHISPER_MAX_MB:
        logger.info(f"  오디오 {file_size_mb:.1f}MB > {WHISPER_MAX_MB}MB — ffmpeg 압축 시작")
        compressed_path = audio_path.replace(".mp3", "_compressed.mp3")
        result = subprocess.run(
            [
                "ffmpeg", "-i", audio_path,
                "-ar", "16000",   # 16kHz (음성 인식에 충분)
                "-ac", "1",       # mono
                "-b:a", "32k",    # 32kbps (~240kB/분)
                "-y", compressed_path,
            ],
            capture_output=True,
        )
        if result.returncode != 0:
            os.remove(audio_path)
            raise RuntimeError(f"오디오 압축 실패: {result.stderr[-200:]}")

        compressed_mb = os.path.getsize(compressed_path) / (1024 * 1024)
        logger.info(f"  압축 완료: {file_size_mb:.1f}MB → {compressed_mb:.1f}MB")

        if compressed_mb > WHISPER_MAX_MB:
            for p in [audio_path, compressed_path]:
                if os.path.exists(p): os.remove(p)
            raise ValueError(f"압축 후에도 {compressed_mb:.1f}MB로 {WHISPER_MAX_MB}MB를 초과합니다. 영상을 짧게 줄여주세요.")

        send_path  = compressed_path
        compressed = True

    try:
        with open(send_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="ko",
                response_format="text",
            )
    finally:
        # 전송 완료 후 원본 + 압축본 모두 삭제
        for p in ([audio_path, send_path] if compressed else [audio_path]):
            if os.path.exists(p):
                os.remove(p)
                logger.info(f"  오디오 파일 삭제: {Path(p).name}")

    text          = transcript if isinstance(transcript, str) else transcript.text
    word_count    = len(text.split())
    est_minutes   = file_size_mb / 1.5  # 원본 크기 기준 WPM 추정
    wpm           = int(word_count / max(est_minutes, 0.1))

    return {"text": text, "wpm": wpm}


# --- 3-4. 트렌드 적합도 점수 산출 ---
async def calculate_trend_score(script_text: str, category: str) -> dict:
    """
    GPT-4o 기반 트렌드 적합도 점수 산출 (TF-IDF fallback 포함)
    Coverage/Novelty 편향 보정 포함
    """
    scores = {}

    # --- GPT-4o 기반 점수 산출 ---
    try:
        top_titles      = PRECOMPUTED.get("top_titles", {}).get(category, [])
        top_titles_text = "\n".join(f"{i+1}. {t}" for i, t in enumerate(top_titles[:20])) if top_titles else "데이터 없음"

        prompt = f"""당신은 유튜브 콘텐츠 트렌드 분석 전문가입니다.
아래 영상 대본과 현재 '{category}' 카테고리의 인기 영상 제목을 비교 분석하여
트렌드 적합도를 평가하세요.

[영상 대본]
{script_text[:3000]}

[인기 영상 제목 Top 20]
{top_titles_text}

반드시 아래 JSON 형식으로만 응답:
{{
  "keyword_score": 0~100,
  "keyword_comment": "대본의 키워드가 트렌드 키워드와 얼마나 부합하는지 한 줄 평가",
  "topic_score": 0~100,
  "topic_comment": "영상 주제가 현재 인기 콘텐츠 방향과 얼마나 일치하는지 한 줄 평가",
  "visual_score": 0~100,
  "visual_comment": "영상 내용이 시각적으로 매력적인 썸네일을 만들기 좋은 소재인지 한 줄 평가",
  "total_comment": "종합 평가 한 줄"
}}"""

        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500,
        )
        content    = response.choices[0].message.content.strip()
        content    = content.replace("```json", "").replace("```", "").strip()
        gpt_result = json.loads(content)

        def _normalize(v) -> int:
            return int(70 + (max(0, min(100, int(v))) / 100) * 30)

        scores["keyword_score"]   = _normalize(gpt_result.get("keyword_score", 50))
        scores["topic_score"]     = _normalize(gpt_result.get("topic_score", 50))
        scores["visual_score"]    = _normalize(gpt_result.get("visual_score", 50))
        scores["keyword_comment"] = gpt_result.get("keyword_comment", "")
        scores["topic_comment"]   = gpt_result.get("topic_comment", "")
        scores["visual_comment"]  = gpt_result.get("visual_comment", "")
        scores["comment"]         = gpt_result.get("total_comment", "")
        logger.info("  GPT-4o 트렌드 점수 산출 완료")

    except Exception as e:
        logger.warning(f"  GPT-4o 트렌드 점수 실패, TF-IDF fallback 사용: {e}")

        # --- TF-IDF fallback ---
        safe_cat = category.replace(" ", "_").replace("&", "and")
        if safe_cat in PRECOMPUTED.get("vectorizer", {}):
            vectorizer     = PRECOMPUTED["vectorizer"][safe_cat]
            category_tfidf = PRECOMPUTED["tfidf"][safe_cat]
            user_tfidf     = vectorizer.transform([script_text])
            sim            = cosine_similarity(user_tfidf, category_tfidf).mean()
            scores["keyword_score"] = min(int(sim * 100 * 2.5), 100)
        else:
            scores["keyword_score"] = 50

        scores["visual_score"] = 50

        if category in PRECOMPUTED.get("top_titles", {}):
            top_text   = " ".join(PRECOMPUTED["top_titles"][category])
            user_words = set(script_text.split())
            top_words  = set(top_text.split())
            if top_words:
                overlap = len(user_words & top_words) / max(len(user_words), 1)
                scores["topic_score"] = min(int(overlap * 100 * 3), 100)
            else:
                scores["topic_score"] = 50
        else:
            scores["topic_score"] = 50

        scores["keyword_comment"] = ""
        scores["topic_comment"]   = ""
        scores["visual_comment"]  = ""

        fallback_total = int(scores["keyword_score"] * 0.4 + scores["visual_score"] * 0.3 + scores["topic_score"] * 0.3)
        if fallback_total >= 80:
            scores["comment"] = "영상의 주제와 핵심 메시지가 명확하며, 시청자에게 강한 호기심을 제공합니다."
        elif fallback_total >= 60:
            scores["comment"] = "트렌드와의 적합도가 양호하나, 제목 키워드와 시각적 요소에서 개선 여지가 있습니다."
        else:
            scores["comment"] = "현재 트렌드와의 차이가 큽니다. 키워드 전략과 썸네일 스타일 재검토를 권장합니다."

    # 종합 점수 (가중합)
    weights = {"keyword_score": 0.4, "visual_score": 0.3, "topic_score": 0.3}
    scores["total"] = int(sum(scores[k] * weights[k] for k in weights))

    # 편향 보정 지표 (TF-IDF 기반 유지)
    scores["bias_metrics"] = calculate_bias_metrics(script_text, category)

    return scores


def calculate_bias_metrics(script_text: str, category: str) -> dict:
    """Coverage & Novelty 편향 보정 지표"""
    if "df" not in PRECOMPUTED:
        return {"coverage": 0, "novelty": 0, "bias_warning": None}

    df     = PRECOMPUTED["df"]
    cat_df = df[df["category_name"] == category] if category in df["category_name"].values else df

    # Coverage
    if len(cat_df) > 0:
        all_tags   = cat_df["tags"].fillna("").str.split("|").explode()
        unique_tags = all_tags[all_tags != ""].nunique()
        total_tags  = len(all_tags[all_tags != ""])
        coverage    = round(unique_tags / max(total_tags, 1) * 100, 1)
    else:
        coverage = 0

    # Novelty
    safe_cat = category.replace(" ", "_").replace("&", "and")
    if safe_cat in PRECOMPUTED.get("vectorizer", {}):
        vectorizer     = PRECOMPUTED["vectorizer"][safe_cat]
        category_tfidf = PRECOMPUTED["tfidf"][safe_cat]
        user_tfidf     = vectorizer.transform([script_text])
        avg_sim        = float(cosine_similarity(user_tfidf, category_tfidf).flatten().mean())
        novelty        = round((1 - avg_sim) * 100, 1)
    else:
        novelty = 50

    return {
        "coverage":     coverage,
        "novelty":      novelty,
        "bias_warning": "해당 카테고리의 인기 영상이 특정 토픽에 집중되어 있습니다." if coverage < 20 else None,
    }


# --- 3-5. GPT-4o 제목 추천 ---
async def generate_titles(script_text: str, category: str, custom_prompt: str) -> list:
    top_titles      = PRECOMPUTED.get("top_titles", {}).get(category, [])
    top_titles_text = "\n".join(top_titles[:10]) if top_titles else "데이터 없음"
    stats           = PRECOMPUTED.get("stats", {}).get(category, {})
    stats_text      = f"평균 조회수: {stats.get('avg_views', 'N/A'):,}" if stats else ""

    prompt = f"""당신은 유튜브 콘텐츠 전략 전문가입니다.
아래 영상 대본과 현재 '{category}' 카테고리의 인기 영상 데이터를 분석하여,
클릭률(CTR)을 극대화할 수 있는 제목 3종을 추천하세요.

[영상 대본 요약]
{script_text[:2000]}

[현재 카테고리 인기 영상 제목 패턴]
{top_titles_text}

[카테고리 통계]
{stats_text}

{f'[사용자 추가 요청] {custom_prompt}' if custom_prompt else ''}

다음 3가지 톤으로 각각 제목을 작성하고, 각 제목에 대해 WHY 근거를 한 줄로 설명하세요:
1. 강렬한 클릭 유도형 (호기심 자극, 의문문/숫자 활용)
2. 감성 스토리형 (감정적 공감, 스토리텔링)
3. 깔끔한 정보형 (명확한 정보 전달)

반드시 아래 JSON 형식으로만 응답하세요:
[
  {{"style": "강렬한 클릭 유도형", "title": "...", "why": "..."}},
  {{"style": "감성 스토리형", "title": "...", "why": "..."}},
  {{"style": "깔끔한 정보형", "title": "...", "why": "..."}}
]"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=1000,
        )
        content = response.choices[0].message.content.strip()
        content = content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except Exception as e:
        logger.error(f"제목 생성 실패: {e}")
        return [{"style": "오류", "title": "제목 생성에 실패했습니다", "why": str(e)}]


# --- 3-6. DALL-E 3 썸네일 생성 ---
async def generate_thumbnails(script_text: str, category: str, custom_prompt: str) -> list:
    """
    DALL-E 3 3종 썸네일을 asyncio.gather로 병렬 생성
    - 키워드 추출 1회 후 3개 DALL-E 호출을 동시에 실행
    - 동기 OpenAI/requests 호출은 asyncio.to_thread로 thread pool에 위임
    """
    styles = [
        {"name": "강렬한 클릭 유도형", "prompt_suffix": "Bold, high-contrast colors with large dramatic text overlay. Eye-catching YouTube thumbnail."},
        {"name": "감성 스토리형",       "prompt_suffix": "Warm, emotional atmosphere with soft lighting. Storytelling-focused YouTube thumbnail."},
        {"name": "깔끔한 정보형",       "prompt_suffix": "Clean, professional design with clear information hierarchy. Minimalist YouTube thumbnail."},
    ]

    # 키워드 추출 (1회, 이후 3개 DALL-E 호출에 공유)
    try:
        kw_resp  = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4o",
            messages=[{"role": "user", "content": f"다음 영상 대본에서 썸네일에 넣을 핵심 키워드 3개를 영어로 추출하세요. 키워드만 쉼표로 구분하여 답하세요:\n\n{script_text[:1000]}"}],
            max_tokens=50,
        )
        keywords = kw_resp.choices[0].message.content.strip()
    except Exception:
        keywords = category

    async def _one_thumbnail(style: dict) -> dict:
        """단일 스타일 썸네일 생성 — DALL-E 호출 + 이미지 다운로드"""
        base_prompt = f"YouTube thumbnail for a video about {keywords}. {style['prompt_suffix']}"
        if custom_prompt:
            base_prompt += f" Additional request: {custom_prompt}"
        try:
            response  = await asyncio.to_thread(
                client.images.generate,
                model="dall-e-3",
                prompt=base_prompt,
                size="1792x1024",
                quality="standard",
                n=1,
            )
            image_url = response.data[0].url
            img_resp  = await asyncio.to_thread(http_requests.get, image_url, timeout=30)
            filename  = f"thumb_{uuid.uuid4().hex[:8]}.png"
            with open(OUTPUTS_DIR / filename, "wb") as f:
                f.write(img_resp.content)
            return {"style": style["name"], "filename": filename, "url": f"/outputs/{filename}", "prompt": base_prompt}
        except Exception as e:
            logger.error(f"썸네일 생성 실패 ({style['name']}): {e}")
            return {"style": style["name"], "filename": None, "url": None, "prompt": base_prompt, "error": str(e)}

    # 3개 동시 실행
    results = await asyncio.gather(*[_one_thumbnail(s) for s in styles])
    return list(results)


# --- 3-7. AI 상세 분석 리포트 ---
async def generate_report(script_text: str, score: dict, category: str) -> str:
    prompt = f"""당신은 유튜브 콘텐츠 전략 컨설턴트입니다.
아래 영상 분석 결과를 바탕으로 상세 컨설팅 리포트를 한국어로 작성하세요.

[카테고리] {category}
[트렌드 적합도 점수] {score.get('total', 0)}/100
  - 제목 키워드 적합도: {score.get('keyword_score', 0)}/100
  - 시각적 트렌드 부합도: {score.get('visual_score', 0)}/100
  - 콘텐츠 주제 관련성: {score.get('topic_score', 0)}/100
[Coverage] {score.get('bias_metrics', {}).get('coverage', 0)}%
[Novelty]  {score.get('bias_metrics', {}).get('novelty', 0)}%

[영상 대본 요약]
{script_text[:2000]}

다음 구조로 리포트를 작성하세요:
1. 영상 강점 (2~3가지)
2. 개선이 필요한 부분 (2~3가지)
3. 구체적 개선 방향 (행동 가능한 제안 3가지)
4. 참신성(Novelty) 평가 — 기존 인기 영상 대비 이 영상만의 차별점"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1500,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"리포트 생성 실패: {e}")
        return f"리포트 생성 중 오류가 발생했습니다: {e}"


# ============================================================
# 4. 완료 작업 자동 정리 (1시간 후)
# ============================================================
def cleanup_old_jobs():
    """완료/실패된 작업을 1시간 후 JOBS 딕셔너리에서 제거"""
    now = datetime.now()
    expired = [
        jid for jid, job in JOBS.items()
        if job["status"] in ("completed", "failed")
        and datetime.fromisoformat(job["created_at"]) < now - timedelta(hours=1)
    ]
    for jid in expired:
        del JOBS[jid]
    if expired:
        logger.info(f"만료 작업 {len(expired)}건 정리 완료")


# ============================================================
# 5. 백그라운드 분석 파이프라인
# ============================================================
async def run_analysis_pipeline(job_id: str, video_path: str, category: str, custom_prompt: str):
    audio_path = ""
    try:
        JOBS[job_id]["status"]   = "processing"
        JOBS[job_id]["progress"] = "영상 전처리 중..."

        # Phase 1: 프레임 추출 + 오디오 분리
        logger.info(f"[{job_id}] Phase 1: 영상 전처리")
        frame_paths = extract_key_frames(video_path)
        audio_path  = extract_audio(video_path)

        # 영상 파일 즉시 삭제 (오디오 추출 완료 후)
        if os.path.exists(video_path):
            os.remove(video_path)
            logger.info(f"[{job_id}] 영상 파일 삭제 완료")

        JOBS[job_id]["progress"] = "음성 분석 중..."

        # Phase 2: Whisper API (내부에서 오디오 파일 삭제)
        logger.info(f"[{job_id}] Phase 2: Whisper API")
        transcript  = transcribe_audio(audio_path)
        audio_path  = ""  # 이미 삭제됨
        script_text = transcript["text"]

        JOBS[job_id]["progress"] = "트렌드 분석 중..."

        # Phase 3: 트렌드 점수
        logger.info(f"[{job_id}] Phase 3: 트렌드 분석")
        score = await calculate_trend_score(script_text, category)

        JOBS[job_id]["progress"] = "AI 콘텐츠 생성 중..."

        # Phase 4: 제목 + 썸네일 + 리포트 병렬 생성
        logger.info(f"[{job_id}] Phase 4: AI 생성 (병렬)")
        titles, thumbnails, report = await asyncio.gather(
            generate_titles(script_text, category, custom_prompt),
            generate_thumbnails(script_text, category, custom_prompt),
            generate_report(script_text, score, category),
        )

        JOBS[job_id].update({
            "status":   "completed",
            "progress": "완료",
            "result": {
                "score":              score,
                "titles":             titles,
                "thumbnails":         thumbnails,
                "report":             report,
                "transcript_preview": script_text[:500],
                "wpm":                transcript["wpm"],
                "frame_count":        len(frame_paths),
                "category":           category,
                "analyzed_at":        datetime.now().isoformat(),
            },
        })
        logger.info(f"[{job_id}] 분석 완료!")

    except Exception as e:
        logger.error(f"[{job_id}] 분석 실패: {e}")
        JOBS[job_id]["status"] = "failed"
        JOBS[job_id]["error"]  = str(e)

    finally:
        # 혹시 남아있는 임시 파일 정리
        for path in [video_path, audio_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass
        # 오래된 작업 정리
        cleanup_old_jobs()


# ============================================================
# 6. API 엔드포인트
# ============================================================

@app.get("/api/health")
async def health():
    """헬스 체크"""
    return {
        "service": "Think:it Pro API",
        "status":  "running",
        "precomputed": {
            "tfidf_categories": len(PRECOMPUTED.get("tfidf", {})),
            "youtube_data":     len(PRECOMPUTED.get("df", pd.DataFrame())),
        },
        "active_jobs": len(JOBS),
    }


@app.get("/api/categories")
async def get_categories():
    """사용 가능한 카테고리 목록"""
    available = list(PRECOMPUTED.get("stats", {}).keys())
    return {"categories": available}


@app.post("/api/analyze")
async def start_analysis(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    category: str    = Form("Entertainment"),
    custom_prompt: str = Form(""),
):
    """영상 분석 시작 — 즉시 job_id 반환, 백그라운드 처리"""
    job_id     = uuid.uuid4().hex[:12]
    video_path = str(UPLOADS_DIR / f"{job_id}_{video.filename}")

    content = await video.read()
    with open(video_path, "wb") as f:
        f.write(content)

    file_size_mb = len(content) / (1024 * 1024)
    logger.info(f"영상 접수: {video.filename} ({file_size_mb:.1f}MB), 카테고리: {category}")

    JOBS[job_id] = {
        "status":     "queued",
        "progress":   "대기 중...",
        "created_at": datetime.now().isoformat(),
        "filename":   video.filename,
        "category":   category,
    }

    background_tasks.add_task(run_analysis_pipeline, job_id, video_path, category, custom_prompt)

    return {
        "job_id":  job_id,
        "status":  "queued",
        "message": "분석이 시작되었습니다.",
    }


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    """분석 작업 진행 상태 및 결과 조회"""
    if job_id not in JOBS:
        return JSONResponse(status_code=404, content={"error": "작업을 찾을 수 없습니다"})

    job      = JOBS[job_id]
    response = {"job_id": job_id, "status": job["status"], "progress": job.get("progress", "")}

    if job["status"] == "completed":
        response["result"] = job["result"]
    elif job["status"] == "failed":
        response["error"] = job.get("error", "알 수 없는 오류")

    return response


@app.post("/api/send-report")
async def send_report(job_id: str = Form(...), email: str = Form(...)):
    """분석 결과를 이메일로 발송"""
    if job_id not in JOBS or JOBS[job_id]["status"] != "completed":
        return JSONResponse(status_code=400, content={"error": "완료된 분석 결과가 없습니다"})

    sender   = os.getenv("EMAIL_SENDER", "")
    password = os.getenv("EMAIL_PASSWORD", "")
    if not sender or not password:
        return {"status": "error", "message": "이메일 설정이 되어있지 않습니다"}

    try:
        result = JOBS[job_id]["result"]
        msg    = MIMEMultipart()
        msg["From"]    = sender
        msg["To"]      = email
        msg["Subject"] = f"[Think:it Pro] AI 컨설팅 리포트 - {result['category']}"

        body = (
            f"Think:it Pro AI 컨설팅 리포트\n{'='*50}\n\n"
            f"트렌드 적합도: {result['score']['total']}/100\n"
            f"{result['score']['comment']}\n\n"
            f"추천 제목:\n"
            + "\n".join(f"  {i+1}. [{t['style']}] {t['title']}" for i, t in enumerate(result["titles"]))
            + f"\n\n상세 분석:\n{result['report']}"
        )
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.send_message(msg)

        return {"status": "sent", "message": f"{email}로 리포트를 발송했습니다"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ============================================================
# 7. 프론트엔드 정적 파일 서빙
# 반드시 모든 API 라우트 정의 이후 마지막에 위치
# ============================================================
app.mount("/", StaticFiles(directory=str(PROJECT_ROOT / "frontend"), html=True), name="frontend")


# ============================================================
# 8. 서버 직접 실행 시
# ============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
