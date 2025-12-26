# @title
import os
from google.colab import userdata

# 1. .streamlit 폴더 생성
os.makedirs(".streamlit", exist_ok=True)

# 2. 코랩 보안 비밀 가져오기
try:
    openai_key = userdata.get('OPENAI_API_KEY')
    email_sender = userdata.get('EMAIL_SENDER')
    email_pw = userdata.get('EMAIL_PASSWORD')

    # 3. secrets.toml 파일 작성
    with open(".streamlit/secrets.toml", "w") as f:
        f.write(f'OPENAI_API_KEY = "{openai_key if openai_key else ""}"\n')
        f.write(f'EMAIL_SENDER = "{email_sender if email_sender else ""}"\n')
        f.write(f'EMAIL_PASSWORD = "{email_pw if email_pw else ""}"\n')
        
    print("✅ 성공: secrets.toml 파일이 생성되었습니다!")
    print(f"   - 발신자: {email_sender}")
    print(f"   - 비밀번호: {'*' * 5} (저장됨)")

except Exception as e:
    print(f"❌ 에러: 보안 비밀을 가져오지 못했습니다. 이름이 정확한지 확인해주세요.\n{e}")
