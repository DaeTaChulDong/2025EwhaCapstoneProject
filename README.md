# Think:it Pro 🎯

> 영상·음성 분석 기반 유튜브 썸네일 생성 · 제목 추천 웹 서비스

**Think:it Pro**는 1인 유튜브 크리에이터를 위한 멀티모달 AI 컨설팅 웹 서비스입니다. 영상을 업로드하면 AI가 음성과 화면을 분석하여 **트렌드 적합도 점수**를 진단하고, 클릭을 부르는 **제목 3종**과 **썸네일 3종**을 자동 생성하며, **통합 컨설팅 리포트**를 제공합니다.

19팀 싱킷 (팀장 이은서, 팀원 양유진·김태언)

---

## 📋 목차

- [프로젝트 소개](#-프로젝트-소개)
- [주요 기능](#-주요-기능)
- [기술 스택](#-기술-스택)
- [소스 코드 구조](#-소스-코드-구조)
- [How to Build](#-how-to-build)
- [How to Install](#-how-to-install)
- [How to Test](#-how-to-test)
- [샘플 데이터 설명](#-샘플-데이터-설명)
- [사용한 오픈소스](#-사용한-오픈소스)

---

## 🎯 프로젝트 소개

### 해결하는 문제 (Pain Points)

1인 크리에이터는 세 가지 어려움을 겪습니다.

1. **정량적 분석 부재** — "왜 내 영상은 안 되는지 이유를 모르겠어요"
2. **리소스 병목** — "썸네일, 제목 기획에만 2~3시간씩 걸려요"
3. **정보 격차** — "1인 크리에이터라서 자본, 기술이 부족해요"

Think:it Pro는 대형 MCN이 독점하던 데이터 분석 역량을 AI로 자동화하여 1인 크리에이터에게 제공합니다.

### 처리 흐름

```
영상 업로드 → 멀티모달 분석(음성+화면) → 트렌드 적합도 진단(0~100)
→ AI 제목 3종 + 썸네일 3종 생성 → 통합 컨설팅 리포트 → 이메일 발송
```

---

## ✨ 주요 기능

| 기능 | 핵심 기술 | 산출물 |
|------|-----------|--------|
| 트렌드 적합도 분석 | YouTube Data API + GPT-4o 의미 분석 | 0~100 종합 점수 + 차원별 세부 점수 |
| AI 제목 추천 | GPT-4o + 인기 영상 패턴 | 3가지 톤 제목 + 추천 근거 |
| AI 썸네일 생성 | DALL-E 3 + 프롬프트 엔지니어링 | 고해상도 썸네일 3종 |
| 편향성 보정 | TF-IDF (Coverage/Novelty) | 추천 편향 방지 지표 |
| 통합 컨설팅 리포트 | GPT-4o | 강점·약점·개선방향 리포트 |
| 이메일 발송 | SMTP | 리포트 이메일 전송 |

---

## 🛠 기술 스택

**Backend**: FastAPI, Uvicorn, Python 3.11
**AI/ML**: OpenAI API (Whisper, GPT-4o, DALL-E 3), scikit-learn (TF-IDF)
**미디어 처리**: OpenCV, ffmpeg
**데이터**: YouTube Data API v3, pandas
**Frontend**: HTML / CSS / JavaScript (SPA)
**배포**: Docker, Oracle Cloud Free Tier

---

## 📂 소스 코드 구조

```
my_yt_consulting/
├── .env.example            # 환경변수 예시 (실제 .env는 직접 생성)
├── .gitignore
├── Dockerfile              # Docker 이미지 빌드 정의
├── requirements.txt        # Python 의존성
├── README.md
├── app/
│   ├── main.py             # FastAPI 메인 서버 + AI 파이프라인
│   └── precompute.py       # YouTube 데이터 수집 + TF-IDF 사전계산
├── data/
│   ├── youtube_top200_data.csv     # 인기 영상 메타데이터 (샘플 포함)
│   ├── precomputed/                # 사전계산 결과
│   │   ├── tfidf_*.npy             # 카테고리별 TF-IDF 벡터
│   │   ├── vectorizer_*.pkl        # 카테고리별 Vectorizer
│   │   ├── category_stats.json     # 카테고리 통계
│   │   └── top_titles.json         # 인기 제목 패턴
│   ├── uploads/            # 업로드 영상 임시 저장 (런타임)
│   └── outputs/            # 생성된 썸네일 저장 (런타임)
└── frontend/
    ├── index.html          # SPA 진입점
    ├── css/                # 스타일
    └── js/                 # 로직 (Fetch API, 폴링)
```

### 핵심 파일 설명

- **`app/main.py`** — FastAPI 서버. Lifespan으로 데이터 사전 로드, BackgroundTasks로 비동기 분석, 5단계 AI 파이프라인(전처리 → 음성분석 → 트렌드분석 → AI생성 → 패키징) 오케스트레이션.
- **`app/precompute.py`** — YouTube Data API로 카테고리별 인기 영상을 수집하고 TF-IDF 벡터·통계·제목 패턴을 사전 계산하여 `data/precomputed/`에 저장.

---

## 🔨 How to Build

### 사전 요구사항

- Docker (권장) 또는 Python 3.11+
- OpenAI API 키 ([발급](https://platform.openai.com/api-keys))
- YouTube Data API v3 키 ([발급](https://console.cloud.google.com/))

### 1. 저장소 클론

```bash
git clone https://github.com/본인계정/my_yt_consulting.git
cd my_yt_consulting
```

### 2. 환경변수 설정

`.env.example`을 복사하여 `.env`를 만들고 본인의 API 키를 입력합니다.

```bash
cp .env.example .env
# .env 파일을 열어 실제 키 입력:
# OPENAI_API_KEY=sk-...
# YOUTUBE_API_KEY=AIza...
```

### 3. (선택) 최신 YouTube 데이터로 사전계산 갱신

저장소에 샘플 데이터가 포함되어 있어 생략 가능합니다. 최신 데이터로 갱신하려면:

```bash
pip install -r requirements.txt
python app/precompute.py
```

> YouTube API 키가 없어도 더미 데이터로 동작합니다(구조 테스트용).

---

## 🚀 How to Install

### 방법 A: Docker (권장)

```bash
# 이미지 빌드
docker build -t my_yt_consulting .

# 컨테이너 실행
docker run -d --name thinkit --restart always \
  -p 8000:8000 --env-file .env my_yt_consulting
```

### 방법 B: 로컬 Python 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# 시스템 패키지 (ffmpeg 필요)
# macOS:  brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg

# 서버 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 접속

브라우저에서 **http://localhost:8000** 으로 접속합니다.

---

## ✅ How to Test

### 1. 서버 상태 확인

```bash
curl http://localhost:8000/api/health
```

정상이면 로드된 데이터 현황(카테고리 수, 영상 수)이 JSON으로 반환됩니다.

### 2. 카테고리 목록 확인

```bash
curl http://localhost:8000/api/categories
```

### 3. 영상 분석 테스트 (웹 UI)

1. http://localhost:8000 접속 후 로그인
2. [영상 업로드]에서 MP4 파일(≤25MB) 업로드
3. 카테고리 선택 후 [AI 분석 시작] 클릭
4. 약 40초~1분 30초 후 결과(점수·제목·썸네일·리포트) 확인

### 4. 영상 분석 테스트 (API 직접 호출)

```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "video=@test.mp4" \
  -F "category=Entertainment" \
  -F "custom_prompt=밝은 톤으로"
# → job_id 반환

curl http://localhost:8000/api/status/{job_id}
# → 진행 상태 및 완료 시 결과 반환
```

---

## 📊 샘플 데이터 설명

저장소에는 즉시 실행 가능하도록 사전계산된 샘플 데이터가 포함되어 있습니다.

| 파일 | 설명 |
|------|------|
| `data/youtube_top200_data.csv` | 14개 카테고리 인기 영상 메타데이터 (제목, 조회수, 태그 등) |
| `data/precomputed/tfidf_*.npy` | 카테고리별 TF-IDF 벡터 행렬 |
| `data/precomputed/vectorizer_*.pkl` | 카테고리별 학습된 TF-IDF Vectorizer |
| `data/precomputed/category_stats.json` | 카테고리별 조회수·좋아요 통계 |
| `data/precomputed/top_titles.json` | 카테고리별 인기 제목 Top 20 |

이 데이터만으로 별도 YouTube API 호출 없이 트렌드 분석이 동작합니다. (단, 영상 분석을 위한 OpenAI API 키는 필요)

> **데이터베이스**: 현재 버전은 별도 DBMS 없이 파일 시스템(CSV/JSON/npy) + 인메모리(JOBS 딕셔너리, 1시간 TTL)로 동작합니다.

---

## 📦 사용한 오픈소스

| 오픈소스 | 용도 | 라이선스 |
|----------|------|----------|
| [FastAPI](https://github.com/tiangolo/fastapi) | 백엔드 웹 프레임워크 | MIT |
| [Uvicorn](https://github.com/encode/uvicorn) | ASGI 서버 | BSD |
| [OpenCV](https://github.com/opencv/opencv-python) | 영상 프레임 추출 | Apache 2.0 |
| [scikit-learn](https://github.com/scikit-learn/scikit-learn) | TF-IDF 벡터화 | BSD |
| [pandas](https://github.com/pandas-dev/pandas) | 데이터 처리 | BSD |
| [openai-python](https://github.com/openai/openai-python) | OpenAI API 클라이언트 | Apache 2.0 |
| [ffmpeg](https://ffmpeg.org/) | 오디오 분리 | LGPL/GPL |

**외부 API**: OpenAI API (Whisper, GPT-4o, DALL-E 3), YouTube Data API v3

---

2026 19팀 싱킷 (Think:it Pro)
