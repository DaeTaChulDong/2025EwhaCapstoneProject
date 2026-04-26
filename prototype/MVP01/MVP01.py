import cv2
import base64
import os
import smtplib
from email.mime.text import MIMEText
from fastapi import FastAPI
from openai import OpenAI
from googleapiclient.discovery import build
from dotenv import load_dotenv

# 1. 환경 설정<-개인적으로 .env파일 생성해서 요소 채워넣어 두어야 합니다. 
load_dotenv("API_KEY.env")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

client = OpenAI(api_key=OPENAI_API_KEY)
app = FastAPI()

def send_email_report(analysis_text):

    if not EMAIL_SENDER or not EMAIL_PASSWORD or not RECEIVER_EMAIL:
        return "이메일 설정 정보 누락"

    # 이메일 본문 구성
    email_body = f"""
    안녕하세요, Think:it AI 분석 로직에 따른 컨설팅 리포트입니다.
    
    [AI 분석 결과]
    {analysis_text}
    
    감사합니다.
    Think:it 팀 드림
    """
    
    msg = MIMEText(email_body)
    msg['Subject'] = "[Think:it] 유튜브 숏츠 트렌드 분석 리포트"
    msg['From'] = EMAIL_SENDER
    msg['To'] = RECEIVER_EMAIL

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, [RECEIVER_EMAIL], msg.as_string())
        return "이메일 발송 성공"
    except Exception as e:
        return f"이메일 발송 실패: {str(e)}"

@app.get("/analyze")
def run_integrated_analysis():
    try:
        video_path = "영상 URL 링크 넣어야 합니다"
        
        # [1] 유튜브 실시간 트렌드 수집
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        request = youtube.videos().list(
            part="snippet", chart="mostPopular", regionCode="KR", videoCategoryId="26", maxResults=5
        )
        yt_res = request.execute()
        trends = ", ".join([item['snippet']['title'] for item in yt_res.get('items', [])])

        # [2] 영상 프레임 추출 (1초당 1장, 총 5장으로 분석력 집중)
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frames_for_ai = []
        
        for i in range(5): # 처음 5초간의 핵심 장면 추출
            cap.set(cv2.CAP_PROP_POS_FRAMES, i * int(fps))
            success, frame = cap.read()
            if success:
                _, buffer = cv2.imencode(".jpg", frame)
                frames_for_ai.append(base64.b64encode(buffer).decode("utf-8"))
        cap.release()

        # [3] AI 분석 (프롬프트 강화)
        prompt = [
            {"role": "system", "content": "너는 유튜브 채널 성장 컨설턴트야. 이미지를 아주 자세히 분석해서 답변해."},
            {"role": "user", "content": [
                f"현재 인기 트렌드는 '{trends}'야. 이 영상의 시각적 특징과 트렌드를 대조해서:",
                "1. 가장 시선을 끄는 베스트 썸네일 장면 번호 추천",
                "2. 클릭률(CTR)을 높일 수 있는 매력적인 제목 3개 제안",
                "3. 100점 만점의 트렌드 점수",
                "위 내용을 반드시 포함해서 한국어로 상세히 리포트를 작성해줘.",
                *[{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{f}"}} for f in frames_for_ai]
            ]}
        ]

        ai_res = client.chat.completions.create(
            model="gpt-4o",
            messages=prompt,
            max_tokens=1000
        )
        report = ai_res.choices[0].message.content
        
        # [4] 이메일 발송
        email_res = send_email_report(report)
        
        return {"status": "success", "analysis": report, "email_status": email_res}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
