%%writefile app.py
import streamlit as st
import os
import time
import base64
import json
import pandas as pd
# [중요] 무거운 라이브러리는 여기서 로드하지 않음 (Lazy Loading)

# =========================================================
# 1. 페이지 설정 & CSS (UI 디자인)
# =========================================================
st.set_page_config(page_title="Think:it Pro", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    /* 메인 타이틀 */
    .main-title { font-size: 2.5rem; font-weight: bold; margin-bottom: 0.5rem; color: #222; }

    /* 섹션 헤더 스타일 */
    .section-header {
        font-size: 1.4rem; font-weight: bold; margin-top: 30px; margin-bottom: 15px;
        color: #333; border-left: 5px solid #FF4B4B; padding-left: 12px;
    }

    /* 점수 원형 UI */
    .score-circle-container { display: flex; justify-content: center; align-items: center; height: 100%; }
    .score-circle {
        position: relative; width: 160px; height: 160px; border-radius: 50%;
        border: 8px solid #FF4B4B; display: flex; justify-content: center;
        align-items: center; flex-direction: column; background-color: #fff;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    .score-num { font-size: 4rem; font-weight: 900; color: #FF4B4B; line-height: 1; }
    .score-max { font-size: 1.2rem; color: #999; font-weight: normal; }
    .score-comment { text-align: center; font-size: 1.2rem; font-weight: bold; color: #555; margin-top: 15px; }

    /* 파일 정보 카드 */
    .info-card {
        background-color: #f8f9fa; border: 1px solid #ddd; border-radius: 12px;
        padding: 20px; height: 100%; display: flex; flex-direction: column; justify-content: center;
    }
    .info-label { font-size: 0.9rem; color: #666; font-weight: bold; }
    .info-value { font-size: 1.2rem; color: #333; font-weight: bold; margin-bottom: 10px; }

    /* 요약 카드 */
    .summary-card {
        background-color: #fff; border: 2px solid #eee; border-radius: 12px;
        padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 20px;
    }

    /* 랭킹 배지 */
    .rank-tag {
        display: block; width: 100%; text-align: center;
        padding: 8px 0; border-radius: 8px; font-weight: bold; color: white; margin-bottom: 10px;
    }
    .bg-1 { background-color: #FFD700; color: #333; }
    .bg-2 { background-color: #C0C0C0; color: #333; }
    .bg-3 { background-color: #CD7F32; color: white; }

    /* 업로더 */
    .stFileUploader { padding: 15px; border: 2px dashed #FF4B4B; border-radius: 15px; text-align: center;}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2. UI 그리기 (초기 화면)
# =========================================================
st.markdown('<div class="main-title">✨ Think:it Pro | AI 컨설팅</div>', unsafe_allow_html=True)

# 데이터 로드
@st.cache_data
def load_benchmark_data():
    if os.path.exists("youtube_top200_data.csv"):
        return pd.read_csv("youtube_top200_data.csv")
    return pd.DataFrame()

df = load_benchmark_data()
cat_list = df['Category_Name'].unique() if not df.empty else ["General", "Vlog", "Gaming"]

# 사이드바
with st.sidebar:
    st.header("📊 설정")
    category = st.selectbox("카테고리 선택", cat_list)
    st.info("💡 Cloudflare Tunnel로 연결되어 훨씬 빠릅니다.")

# 메인 업로더
with st.expander("📤 영상 파일 업로드 (MP4)", expanded=True):
    uploaded_file = st.file_uploader("여기에 파일을 드래그하거나 선택하세요", type=["mp4"])

# =========================================================
# 3. 분석 로직 (버튼 클릭 시 실행)
# =========================================================
if uploaded_file:
    tfile = "temp_input.mp4"
    with open(tfile, "wb") as f:
        f.write(uploaded_file.read())
    
    if st.button("🚀 AI 데이터 분석 시작 (Click)", type="primary", use_container_width=True):
        
        with st.status("⚙️ AI 엔진 및 라이브러리 로딩 중...", expanded=True) as status:
            # 라이브러리 로딩
            try:
                import torch
                import cv2
                from moviepy.editor import VideoFileClip
                from openai import OpenAI
                from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
                from google.colab import userdata
                import numpy as np
                import re
                from collections import Counter
            except ImportError as e:
                st.error(f"라이브러리 로딩 실패: {e}")
                st.stop()

            # API 키 확인
            try:
                api_key = userdata.get('OPENAI_API_KEY')
                client = OpenAI(api_key=api_key)
            except:
                try:
                    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                except:
                    st.error("🚨 API 키 오류! 보안 비밀을 확인하세요.")
                    st.stop()

            # 모델 로드
            @st.cache_resource
            def load_models():
                device = "cuda:0" if torch.cuda.is_available() else "cpu"
                torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
                model_id = "openai/whisper-large-v3"
                model = AutoModelForSpeechSeq2Seq.from_pretrained(
                    model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
                )
                model.to(device)
                processor = AutoProcessor.from_pretrained(model_id)
                pipe = pipeline(
                    "automatic-speech-recognition", model=model, tokenizer=processor.tokenizer,
                    feature_extractor=processor.feature_extractor, max_new_tokens=128,
                    chunk_length_s=30, batch_size=16, return_timestamps=True,
                    torch_dtype=torch_dtype, device=device,
                )
                return pipe

            st.write("🎙️ Whisper 모델 준비 중...")
            whisper_pipe = load_models()
            
            # 데이터 추출
            st.write("👀 영상 및 오디오 데이터 추출 중...")
            clip = VideoFileClip(tfile)
            audio_path = "temp_audio.mp3"
            clip.audio.write_audiofile(audio_path, logger=None)
            transcription = whisper_pipe(audio_path, generate_kwargs={"language": "korean"})
            text = transcription["text"]
            duration = clip.duration
            wpm = (len(text.split()) / duration) * 60
            
            # Vision
            cap = cv2.VideoCapture(tfile)
            frames_data = []
            timestamps = [duration * 0.15, duration * 0.5, duration * 0.85]
            
            def encode_image(img):
                _, buffer = cv2.imencode('.jpg', img)
                return base64.b64encode(buffer).decode('utf-8')

            for t in timestamps:
                cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
                ret, frame = cap.read()
                if ret:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    frames_data.append({
                        "img": frame_rgb, "time_str": time.strftime('%M:%S', time.gmtime(t)),
                        "time_sec": t,
                        "b64": encode_image(frame_bgr)
                    })
            cap.release()
            clip.close()
            if os.path.exists(audio_path): os.remove(audio_path)

            # GPT-4o 분석
            st.write("🧠 GPT-4o 심층 분석 중...")
            prompt = f"""
            당신은 데이터 기반의 냉철한 '유튜브 전문 컨설턴트'입니다.
            현재 분석할 영상의 카테고리는 '{category}'입니다.
            [사용자 영상 데이터]
            - 대본(Script): {text[:1500]}... (일부 발췌)
            - 발화 속도(WPM): {int(wpm)}
            
            제공된 시각 데이터(썸네일 후보 프레임)와 대본을 종합하여 분석하세요.
            반드시 아래 JSON 포맷을 준수하여 '한국어'로 응답해야 합니다.
            {{
                "score": (0~100 사이의 정수 점수),
                "score_comment": (점수에 대한 한 줄 코멘트),
                "summary_points": ["핵심 전략 1", "핵심 전략 2"],
                "scene_reasons": ["1순위 이유", "2순위 이유", "3순위 이유"],
                "titles": [
                    {{"text": "제목 1", "why": "이유"}},
                    {{"text": "제목 2", "why": "이유"}},
                    {{"text": "제목 3", "why": "이유"}}
                ],
                "detail_analysis": (상세 분석 피드백)
            }}
            """
            
            content = [{"type": "text", "text": prompt}]
            for fd in frames_data:
                content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{fd['b64']}"}})
            
            response = client.chat.completions.create(
                model="gpt-4o", messages=[{"role": "user", "content": content}], response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content)
            status.update(label="✅ 분석 완료!", state="complete", expanded=False)

        # =========================================================
        # 4. 결과 UI 구현 (요청하신 순서대로 배치)
        # =========================================================
        st.divider()

        # ---------------------------------------------------------
        # [1] 상단: (왼쪽) 종합 점수 / (오른쪽) 파일 정보
        # ---------------------------------------------------------
        col_top_L, col_top_R = st.columns([1, 1], gap="medium")

        with col_top_L:
            st.markdown('<div class="section-header" style="text-align:center;">🏆 종합 트렌드 적합도</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="score-circle-container">
                <div class="score-circle">
                    <div class="score-num">{result['score']}</div>
                    <div class="score-max">/ 100</div>
                </div>
            </div>
            <div class="score-comment">{result['score_comment']}</div>
            """, unsafe_allow_html=True)

        with col_top_R:
            st.markdown('<div class="section-header">📁 파일 정보</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="info-card">
                <div><span class="info-label">파일명</span><div class="info-value">{uploaded_file.name}</div></div>
                <div style="margin-top:15px;"><span class="info-label">카테고리</span><div class="info-value">{category}</div></div>
                <div style="margin-top:15px;"><span class="info-label">발화 속도</span><div class="info-value">{int(wpm)} WPM</div></div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # ---------------------------------------------------------
        # [2] 중단: 1, 2, 3순위 장면 (같은 사이즈로 가로 배치)
        # ---------------------------------------------------------
        st.markdown('<div class="section-header">📸 썸네일 장면 추천 (Best 3)</div>', unsafe_allow_html=True)
        
        # 3개의 동일한 크기 컬럼 생성
        thumb_c1, thumb_c2, thumb_c3 = st.columns(3, gap="medium")

        with thumb_c1:
            st.markdown(f'<span class="rank-tag bg-1">🥇 1순위 ({frames_data[0]["time_str"]})</span>', unsafe_allow_html=True)
            st.video(tfile, start_time=int(frames_data[0]['time_sec']))
            st.caption(f"💡 {result['scene_reasons'][0]}")

        with thumb_c2:
            st.markdown(f'<span class="rank-tag bg-2">🥈 2순위 ({frames_data[1]["time_str"]})</span>', unsafe_allow_html=True)
            st.video(tfile, start_time=int(frames_data[1]['time_sec']))
            st.caption(f"💡 {result['scene_reasons'][1]}")

        with thumb_c3:
            st.markdown(f'<span class="rank-tag bg-3">🥉 3순위 ({frames_data[2]["time_str"]})</span>', unsafe_allow_html=True)
            st.video(tfile, start_time=int(frames_data[2]['time_sec']))
            st.caption(f"💡 {result['scene_reasons'][2]}")

        st.markdown("---")

        # ---------------------------------------------------------
        # [3] 하단: 나머지 정보 순차적 디스플레이 (한 줄씩)
        # ---------------------------------------------------------
        
        # (3-1) 핵심 전략 요약
        st.markdown('<div class="section-header">📍 핵심 전략 요약</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="summary-card">
            <ul style="font-size: 1.1rem; line-height: 1.8;">
                <li><b>전략 1:</b> {result['summary_points'][0]}</li>
                <li><b>전략 2:</b> {result['summary_points'][1]}</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # (3-2) 제목 추천
        st.markdown('<div class="section-header" style="margin-top: 40px;">🏷️ 클릭을 부르는 제목 추천</div>', unsafe_allow_html=True)
        for i, t in enumerate(result['titles']):
            with st.expander(f"📝 추천 {i+1}: {t['text']}", expanded=True):
                st.info(f"**WHY?** {t['why']}")

        # (3-3) 상세 분석
        st.markdown('<div class="section-header" style="margin-top: 40px;">📊 AI 상세 분석 리포트</div>', unsafe_allow_html=True)
        with st.container():
            st.markdown(f"""
            <div style="background-color:#fff; padding:20px; border-radius:10px; border:1px solid #ddd; line-height:1.6;">
                {result['detail_analysis']}
            </div>
            """, unsafe_allow_html=True)
