# @title
#셀1: 라이브러리 설치
!pip install google-api-python-client oauth2client \
             streamlit pyngrok openai yt-dlp chromadb \
             torch transformers accelerate librosa opencv-python-headless moviepy tqdm
!sudo apt-get update && sudo apt-get install -y ffmpeg

!pip install -q streamlit openai moviepy opencv-python-headless pandas numpy torch torchvision torchaudio transformers accelerate
