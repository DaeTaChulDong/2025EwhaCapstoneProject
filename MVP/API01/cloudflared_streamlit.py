# 1. Cloudflared 설치
!wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
!chmod +x cloudflared-linux-amd64

# 2. Streamlit 실행 (Cloudflared 터널링 사용)
# 실행 후 나오는 "trycloudflare.com" 으로 끝나는 링크를 클릭하세요.
!streamlit run app.py & ./cloudflared-linux-amd64 tunnel --url http://localhost:8501
