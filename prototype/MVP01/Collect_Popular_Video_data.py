import os
import base64
from googleapiclient.discovery import build
from openai import OpenAI
from dotenv import load_dotenv

# 1. 환경 변수 로드 (.env 파일에 YOUTUBE_API_KEY, OPENAI_API_KEY)
load_dotenv("API_KEY.env")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

def get_success_formula():
   
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

    # 2. 'Howto & Style' (ID: 26) 인기 영상 30개 수집
    request = youtube.videos().list(
        part="snippet,statistics",
        chart="mostPopular",
        regionCode="KR",
        videoCategoryId="26",
        maxResults=30
    )
    response = request.execute()

    # 데이터 정리: 제목과 썸네일 URL 추출
    trends_data = []
    for item in response.get('items', []):
        trends_data.append({
            "title": item['snippet']['title'],
            "thumbnail_url": item['snippet']['thumbnails']['high']['url'] # 고화질 썸네일
        })

    # 3. OpenAI GPT-4o 멀티모달 분석
    # 썸네일 URL들을 메시지에 포함시켜 시각적 패턴 분석 요청
    print("\n--- AI가 30개의 인기 영상 데이터를 분석 중입니다... ---\n")
    
    # 분석용 프롬프트 구성
    analysis_prompt = (
        "너는 유튜브 콘텐츠 전략 전문가야. 아래 제공된 30개의 인기 영상 제목과 썸네일 정보를 분석해서 "
        "현재 'Howto & Style' 카테고리의 시각적 성공 공식과 키워드 트렌드를 도출해줘.\n\n"
    )
    
    # 텍스트 데이터 추가
    for idx, data in enumerate(trends_data):
        analysis_prompt += f"{idx+1}. 제목: {data['title']}\n"

    # OpenAI 메시지 구조 생성 (멀티모달 처리)
    content_list = [{"type": "text", "text": analysis_prompt}]
    
    # 상위 30개 영상의 썸네일 이미지 시각적으로 직접 분석 
    for data in trends_data[:30]:
        content_list.append({
            "type": "image_url",
            "image_url": {"url": data['thumbnail_url']}
        })

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": content_list}],
        max_tokens=1000
    )

    print("=== [성공 공식 도출 결과] ===\n")
    print(response.choices[0].message.content)

if __name__ == "__main__":
    if not YOUTUBE_API_KEY or not OPENAI_API_KEY:
        print("에러: .env 파일에 API 키들을 설정해주세요!")
    else:
        get_success_formula()
