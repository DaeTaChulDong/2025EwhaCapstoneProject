
!sudo apt-get update && sudo apt-get install -y ffmpeg


!pip install streamlit pyngrok openai yt-dlp chromadb \
             torch transformers accelerate librosa opencv-python-headless moviepy
# ---------------------------------------------------------
%%writefile app.py

import streamlit as st
import os
import cv2
import json
import base64
import torch
import chromadb
import numpy as np
from datetime import datetime
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from openai import OpenAI
from moviepy.editor import VideoFileClip # ★ 안전한 변환을 위한 라이브러리

# ---------------------------------------------------------
# 1. 환경 설정 & 키 로드 (Streamlit Secrets 사용)
# ---------------------------------------------------------
st.set_page_config(page_title="Think:it", layout="wide")

try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except:
    st.error("🚨 [오류] 키가 전달되지 않았습니다. 서버 실행 코드를 확인하세요.")
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

# 데이터 경로
BASE_DIR = "/content/thinkit_data"
os.makedirs(BASE_DIR, exist_ok=True)

# 모델 로드 (캐싱)
@st.cache_resource
def load_whisper_model():
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    
    model_id = "openai/whisper-large-v3"
    
    try:
        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
        )
        model.to(device)
        processor = AutoProcessor.from_pretrained(model_id)
        
        pipe = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            max_new_tokens=128,
            chunk_length_s=30,
            batch_size=16,
            return_timestamps=True,
            torch_dtype=torch_dtype,
            device=device,
        )
        return pipe
    except Exception as e:
        st.error(f"Whisper 모델 로딩 실패: {e}")
        return None

pipe = load_whisper_model()

# ---------------------------------------------------------
# 2. 분석 함수 (Logic)
# ---------------------------------------------------------
def extract_data(video_path):
    if pipe is None: return "", 0, []

    # [수정] A. 오디오 추출 (MoviePy 사용 - 훨씬 안정적임)
    audio_path = "temp_audio.mp3"
    
    try:
        # 비디오 파일 로드
        video_clip = VideoFileClip(video_path)
        
        # 오디오가 있는지 확인
        if video_clip.audio is None:
            return "", 0, [] # 오디오 없음
            
        # 오디오 파일로 저장
        video_clip.audio.write_audiofile(audio_path, logger=None) # 로그 숨김
        video_clip.close()
        
        # B. Whisper 분석 (생성된 mp3 파일 읽기)
        audio_result = pipe(audio_path, generate_kwargs={"language": "korean"})
        full_text = audio_result["text"]
        duration = audio_result.get("chunks", [])[-1]['timestamp'][1] if audio_result.get("chunks") else 1
        wpm = (len(full_text.split()) / duration * 60)
        
    except Exception as e:
        st.error(f"오디오 처리 중 에러 발생: {e}")
        return "", 0, []
        
    finally:
        # 임시 오디오 파일 삭제
        if os.path.exists(audio_path):
            os.remove(audio_path)
    
    # C. Visual Analysis
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    frames = []
    if total_frames > 30: points = [0.2, 0.5, 0.8]
    else: points = [0.5]
        
    for point in points:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(total_frames * point))
        success, frame = cap.read()
        if success:
            frame = cv2.resize(frame, (640, 360))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(frame)
    cap.release()
    
    return full_text, wpm, frames

# ---------------------------------------------------------
# 3. UI 구성
# ---------------------------------------------------------
st.title("🎬 Think:it | AI 유튜브 컨설턴트")
st.markdown("당신의 영상을 업로드하세요. **성공 공식**과 비교하여 솔루션을 제공합니다.")

with st.sidebar:
    st.header("설정")
    category = st.selectbox("카테고리 선택", ["Vlog (일상)", "Entertainment (예능)", "Cooking (요리)", "Tech (IT)"])
    st.info(f"💡 현재 '{category}' 카테고리의 성공 공식을 적용 중입니다.")
    
    st.markdown("---")
    st.caption("오늘의 성공 공식 (Updated 09:00)")
    st.markdown(f"""
    - **WPM**: 160 ~ 190
    - **키워드**: '충격', '결말'
    - **스타일**: 고채도, 얼굴 클로즈업
    """)

uploaded_file = st.file_uploader("분석할 영상 파일 업로드 (MP4)", type=["mp4"])

if uploaded_file is not None:
    # 안전한 파일명 사용
    temp_path = "input_video.mp4"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.video(temp_path)
    
    if st.button("🚀 AI 분석 시작하기", type="primary"):
        with st.spinner('AI가 영상을 보고, 듣고, 분석하는 중입니다... (약 1분 소요)'):
            try:
                # 1. 데이터 추출
                text, wpm, frames = extract_data(temp_path)
                
                if not text:
                    st.warning("⚠️ 영상에서 목소리를 찾을 수 없습니다. (혹은 오디오 트랙이 없는 영상입니다)")
                else:
                    # 2. GPT-4o 컨설팅
                    prompt = f"""
                    You are a YouTube Consultant.
                    Category: {category}
                    User Data -> WPM: {wpm:.1f}, Script: {text[:300]}...
                    
                    Provide a JSON response in Korean:
                    {{
                        "score": (int 0-100),
                        "comment": (one line summary),
                        "title_ideas": ["title1", "title2", "title3"],
                        "feedback": {{"audio": "...", "visual": "..."}}
                    }}
                    """
                    
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt}],
                        response_format={"type": "json_object"}
                    )
                    result = json.loads(response.choices[0].message.content)
                    
                    # 4. 결과 리포트 화면
                    st.divider()
                    st.subheader("📊 분석 결과 리포트")
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("트렌드 적합도", f"{result['score']}점")
                    col2.metric("말하기 속도 (WPM)", f"{int(wpm)}")
                    col3.info(f"{result['comment']}")
                    
                    st.subheader("🖼️ AI 추천 썸네일 장면")
                    if frames:
                        img_cols = st.columns(len(frames))
                        for i, frame in enumerate(frames):
                            with img_cols[i]:
                                st.image(frame, caption=f"추천 후보 {i+1}", use_container_width=True)
                    
                    st.subheader("✍️ 클릭을 부르는 제목 추천")
                    for title in result['title_ideas']:
                        st.success(f"📌 {title}")
                        
                    with st.expander("📝 상세 피드백 보기"):
                        st.write(f"**🔊 오디오:** {result['feedback']['audio']}")
                        st.write(f"**🎨 비주얼:** {result['feedback']['visual']}")

            except Exception as e:
                st.error(f"에러 발생: {e}")
            finally:
                if os.path.exists(temp_path): os.remove(temp_path)

# ---------------------------------------------------------

import time
import os
from pyngrok import ngrok
from google.colab import userdata

print("🔐 [시스템] Streamlit 비밀 설정 파일 생성 중...")

try:
    # 1. 코랩 Secrets에서 키 가져오기
    OPENAI_API_KEY = userdata.get('OPENAI_API_KEY')
    NGROK_AUTH_TOKEN = userdata.get('NGROK_AUTH_TOKEN')
    
    # 2. .streamlit 폴더 및 secrets.toml 파일 생성 (자동)
    os.makedirs(".streamlit", exist_ok=True)
    with open(".streamlit/secrets.toml", "w") as f:
        f.write(f'OPENAI_API_KEY = "{OPENAI_API_KEY}"')
    
    print("✅ 비밀 파일 생성 완료! (환경 변수 오류 해결)")
    
    # 3. Ngrok 인증
    ngrok.set_auth_token(NGROK_AUTH_TOKEN)

except Exception as e:
    print(f"\n🚨 [오류] 키 로드 실패: {e}")
    print("👉 왼쪽 열쇠 아이콘 > 키 이름 & '노트북 액세스' ON 확인 필수")
    raise e

# 4. 기존 프로세스 종료
ngrok.kill()

# 5. Streamlit 실행 (이제 파일에서 키를 읽어옵니다)
get_ipython().system_raw('streamlit run app.py &')

# 6. 대기
print("⏳ 서버 시작 중... (5초)")
time.sleep(5)

# 7. 주소 생성
try:
    public_url = ngrok.connect(8501)
    print(f"\n========================================================")
    print(f"🎉 Think:it 웹사이트가 생성되었습니다!")
    print(f"👉 접속 주소: {public_url.public_url}")
    print(f"========================================================\n")
except Exception as e:
    print(f"❌ 에러: {e}")
