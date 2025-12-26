# Think:it Pro - AI 유튜브 영상 컨설팅 & 썸네일 생성 서비스

## 1. 프로젝트 개요
이 프로젝트는 사용자가 업로드한 영상(MP4)을 AI가 시각(Vision)과 청각(Audio)으로 분석하여,
실제 유튜브 트렌드 데이터(Top 200)와 비교 분석한 후 구체적인 솔루션을 제공하는 웹 서비스입니다.
OpenAI GPT-4o, Whisper, DALL-E 3 모델을 활용하여 전문적인 피드백과 생성형 이미지를 제공합니다.

## 2. 구동 환경 (System Requirements)
* **OS:** Linux (Google Colab 환경 권장), Windows, macOS
* **Python:** 3.8 이상
* **GPU:** NVIDIA GPU 권장 (Whisper-large 모델 구동 시 VRAM 10GB 이상 필요)
    * *Google Colab 사용 시 A100 또는 T4 GPU 환경 권장*
* **Network:** 외부 인터넷 연결 필수 (OpenAI API 및 Cloudflare Tunnel 사용)

## 3. 필수 라이브러리 (Dependencies)
아래 라이브러리들이 설치되어 있어야 합니다. (requirements.txt)

streamlit          # 웹 UI 프레임워크
openai             # GPT-4o 및 DALL-E 3 API 사용
torch              # 딥러닝 모델 구동 (Whisper)
transformers       # HuggingFace 모델 로드
accelerate         # 모델 가속화
pandas             # CSV 데이터 처리
opencv-python      # 비디오 프레임 추출 (cv2)
moviepy            # 오디오 추출 및 변환
numpy              # 수치 연산
requests           # 이미지 다운로드 요청

## 4. 주요 기능 (Key Features)

### A. 멀티모달 영상 분석 (AI Analysis)
1.  **자동 대본 추출 (STT):** Whisper Large-v3 모델을 사용하여 영상 내 한국어 음성을 텍스트로 변환
2.  **발화 속도(WPM) 측정:** 영상 길이 대비 단어 수를 계산하여 전달력 분석
3.  **주요 장면 추출 (Vision):** 영상의 초반(Hook), 중반, 후반부 핵심 프레임을 이미지로 추출

### B. 데이터 기반 컨설팅 (Consulting)
1.  **종합 트렌드 점수 산출:** 실제 유튜브 인기 영상 데이터(CSV)와 비교하여 60~100점 척도로 평가
2.  **클릭을 부르는 제목 추천:** 트렌드 키워드를 반영한 3가지 제목 제안 (호기심형, 정보형 등)
3.  **전략 요약 및 상세 피드백:** 개선이 필요한 부분을 구체적인 텍스트로 리포팅

### C. 썸네일 솔루션 (Thumbnail)
1.  **장면 캡처 다운로드:** 영상 내 Best 3 장면을 고화질 이미지로 다운로드 제공
2.  **AI 생성 썸네일 (DALL-E 3):** 분석 내용을 바탕으로 클릭률(CTR)을 높이는 구도의 썸네일 이미지 자동 생성 및 다운로드

### D. 리포트 발송 (Email Report)
* 분석된 전체 결과를 사용자가 입력한 이메일 주소로 즉시 발송 (SMTP 연동)

## 5. 설정 및 실행 방법 (Setup & Run)

### 1) 보안 키 설정 (Secrets)
Google Colab의 '보안 비밀(Secrets)' 또는 로컬의 `.streamlit/secrets.toml` 파일에 아래 키를 설정해야 합니다.
* `OPENAI_API_KEY`: OpenAI API 키 (GPT-4o, DALL-E 3 사용)
* `EMAIL_SENDER`: 발송자 이메일 주소 (Gmail 권장)
* `EMAIL_PASSWORD`: 이메일 앱 비밀번호 (SMTP 인증용)
* `YOUTUBE_API_KEY`: Youtube Data API 키

### 2) 데이터 파일 준비

앞서 유튜브 API KEY를 통해서 VideoCollect를 돌려서 만든 `youtube_top200_data.csv` 파일이 카테고리별 벤치마크 데이터가 포함된 프로젝트 루트 경로에 있어야 합니다.

### 3) 실행 명령어
Google Colab에서 실행 시 Cloudflared를 이용해 외부 URL을 생성합니다.

# 필요한 패키지 설치
!pip install streamlit openai moviepy transformers accelerate

# 앱 실행 (Cloudflare Tunnel 사용)
!wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
!chmod +x cloudflared-linux-amd64
!streamlit run app.py & ./cloudflared-linux-amd64 tunnel --url http://localhost:8501

## 6. 주의 사항
* 이메일 발송 기능은 Google 계정의 '앱 비밀번호' 생성이 선행되어야 작동합니다.
* Whisper Large 모델은 최초 실행 시 다운로드 시간이 소요될 수 있습니다.
