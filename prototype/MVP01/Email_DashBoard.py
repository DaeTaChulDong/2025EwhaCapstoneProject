import os
import cv2
import base64
import smtplib
from email.mime.text import MIMEText
from fastapi import FastAPI
from openai import OpenAI
from googleapiclient.discovery import build
from dotenv import load_dotenv

# 1. 환경 설정
load_dotenv("API_KEY.env")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app = FastAPI()

# 이메일 설정 (Gmail 기준)
EMAIL_SENDER = os.getenv("EMAIL_SENDER")  # 내 이메일
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # 앱 비밀번호
RECEIVER_EMAIL = "받는_사람_이메일@gmail.com"

def send_email_report(content):
    """분석 결과를 이메일로 발송합니다."""
    msg = MIMEText(content)
    msg['Subject'] = "[SyncIt] 당신의 영상 분석 리포트가 도착했습니다."
    msg['From'] = EMAIL_SENDER
    msg['To'] = RECEIVER_EMAIL

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, RECEIVER_EMAIL, msg.as_string())
        print("이메일 발송 성공!")
    except Exception as e:
        print(f"이메일 발송 실패: {e}")

def get_trends():
    youtube = build('youtube', 'v3', developerKey=os.getenv("YOUTUBE_API_KEY"))
    request = youtube.videos().list(part="snippet", chart="mostPopular", regionCode="KR", videoCategoryId="26", maxResults=5)
    response = request.execute()
    return ", ".join([item['snippet']['title'] for item in response.get('items', [])])

@app.get("/analyze")
def run_analysis():
    video_path = "6306039-uhd_2160_4096_24fps.mp4"
    trends = get_trends()
    
    # 영상 프레임 추출 (간략화)
    cap = cv2.VideoCapture(video_path)
    success, frame = cap.read()
    _, buffer = cv2.imencode(".jpg", frame)
    base64_image = base64.b64encode(buffer).decode("utf-8")
    cap.release()

    # AI 분석
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": f"트렌드({trends})에 맞게 이 영상을 분석하고 제목 3개를 추천해줘."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]
        }]
    )
    
    report = response.choices[0].message.content
    
    # 이메일 발송 호출
    send_email_report(report)
    
    return {"status": "success", "analysis": report}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
