import cv2
import base64
import os
from openai import OpenAI
from googleapiclient.discovery import build
from dotenv import load_dotenv
import matplotlib.pyplot as plt

# 1. 환경 설정 및 API 로드
load_dotenv("API_KEY.env")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# 유튜브 API를 통해 실시간 트렌드(제목)를 가져옴
def get_realtime_youtube_trends():
  
    print("--- 유튜브 실시간 트렌드 수집 중... ---")
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    
    # Howto & Style (ID: 26) 카테고리 인기 영상 10개 수집 [cite: 104]
    request = youtube.videos().list(
        part="snippet",
        chart="mostPopular",
        regionCode="KR",
        videoCategoryId="26",
        maxResults=10
    )
    response = request.execute()
    
    titles = [item['snippet']['title'] for item in response.get('items', [])]
    return ", ".join(titles)

def analyze_video_vs_trend(video_path):
    # 1. 유튜브 실시간 트렌드 제목 데이터 가져오기 
    realtime_formula = get_realtime_youtube_trends()
    
    print(f"--- 영상 분석 시작: {video_path} ---")
    
    # 2. 영상 프레임 추출 (1초당 1장) - 경량화 전략 
    video_capture = cv2.VideoCapture(video_path)
    fps = video_capture.get(cv2.CAP_PROP_FPS)
    frames = []
    display_frames = []
    
    count = 0
    while video_capture.isOpened():
        success, frame = video_capture.read()
        if not success: break
        
        if count % int(fps) == 0:
            _, buffer = cv2.imencode(".jpg", frame)
            encoded_image = base64.b64encode(buffer).decode("utf-8")
            frames.append(encoded_image)
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            display_frames.append(rgb_frame)
        count += 1
    video_capture.release()

    # 3. OpenAI GPT-4o 멀티모달 대조 분석 [cite: 111, 113]
    print(f"--- {len(frames)}개의 프레임을 수집된 {len(realtime_formula.split(','))}개 트렌드와 대조 중... ---")
    
    prompt = [
        {
            "role": "system",
            "content": "너는 유튜브 CTR 최적화 전문가야. 실시간 유튜브 인기 제목 트렌드와 사용자의 영상을 비교해줘."
        },
        {
            "role": "user",
            "content": [
                f"현재 유튜브 인기 제목 트렌드 키워드들이야: {realtime_formula}",
                "이 트렌드 키워드들이 주는 '감성'과 '주제'를 고려할 때, 첨부된 영상 프레임 중 썸네일로 가장 적합한 장면을 골라줘.",
                "또한 트렌드에 맞는 추천 제목 3가지를 제안하고, 100점 만점의 '트렌드 일치 점수'를 내줘.",
                *[{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{f}"}} for f in frames[:10]]
            ]
        }
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=prompt,
        max_tokens=1000
    )
    
    analysis_result = response.choices[0].message.content
    print("\n=== AI 통합 컨설팅 리포트 ===\n")
    print(analysis_result)
    
    # 4. 시각화
    visualize_results(display_frames)

def visualize_results(frames):
    plt.figure(figsize=(15, 5))
    plt.suptitle("SyncIt Analysis: Current Trends vs Your Video", fontsize=16)
    num_to_show = min(len(frames), 5)
    for i in range(num_to_show):
        plt.subplot(1, num_to_show, i + 1)
        plt.imshow(frames[i])
        plt.title(f"Frame {i}s")
        plt.axis('off')
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    video_file = "6306039-uhd_2160_4096_24fps.mp4"
    
    if os.path.exists(video_file):
        analyze_video_vs_trend(video_file)
    else:
        print(f"파일을 찾을 수 없습니다: {video_file}")
