# @title
#셀2: 인기 영상 10개 카테고리 각 20개 영상의 메타데이터 추출하여 csv로 저장
import googleapiclient.discovery
import pandas as pd
import os

# --------------------------------------------------------
# 1. API 키 자동 로드 (Google Colab 보안 비밀)
# --------------------------------------------------------
try:
    from google.colab import userdata
    API_KEY = userdata.get('YOUTUBE_API_KEY')
    print(f"성공: API 키를 로드했습니다. (Key: {API_KEY[:5]}...)")
except ImportError:
    API_KEY = None
    print("주의: 로컬 환경입니다. API 키를 직접 설정해주세요.")

YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# --------------------------------------------------------
# 2. 수집할 카테고리 (주요 10개)
# --------------------------------------------------------
TARGET_CATEGORIES = {
    22: "People & Blogs",        # 인터뷰, 브이로그
    24: "Entertainment",         # 예능, 토크쇼
    25: "News & Politics",       # 뉴스
    1:  "Film & Animation",      # 영화/애니
    10: "Music",                 # 음악
    17: "Sports",                # 스포츠
    20: "Gaming",                # 게임
    23: "Comedy",                # 코미디
    26: "Howto & Style",         # 정보/노하우
    28: "Science & Technology"   # 과학/기술
}

def get_videos_by_category(api_key, category_dict, target_count=20):
    """
    각 카테고리별로 인기 동영상을 target_count(20개)만큼 수집합니다.
    """
    if not api_key:
        print("Error: 유효한 API 키가 없습니다.")
        return pd.DataFrame()

    youtube = googleapiclient.discovery.build(
        YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=api_key
    )
    
    all_videos = []
    print(f"\n[{len(category_dict)}개 카테고리 x {target_count}개 영상] 수집을 시작합니다...\n")

    for cat_id, cat_name in category_dict.items():
        try:
            print(f"waiting... [{cat_name}] 데이터 가져오는 중")
            
            # API 요청 (maxResults를 20으로 설정)
            request = youtube.videos().list(
                part="snippet,statistics",
                chart="mostPopular",
                regionCode="KR",
                videoCategoryId=str(cat_id),
                maxResults=target_count
            )
            response = request.execute()

            items = response.get('items', [])
            
            # 가져온 영상 개수만큼 반복
            for item in items:
                snippet = item['snippet']
                statistics = item['statistics']
                
                # 썸네일 고화질 우선 추출
                thumbnails = snippet.get('thumbnails', {})
                if 'maxres' in thumbnails:
                    thumb_url = thumbnails['maxres']['url']
                elif 'standard' in thumbnails:
                    thumb_url = thumbnails['standard']['url']
                elif 'high' in thumbnails:
                    thumb_url = thumbnails['high']['url']
                else:
                    thumb_url = thumbnails.get('default', {}).get('url')

                video_data = {
                    'Category_ID': cat_id,
                    'Category_Name': cat_name,
                    'Video_Title': snippet['title'],
                    'Channel_Title': snippet['channelTitle'],
                    'View_Count': statistics.get('viewCount', 0),
                    'Like_Count': statistics.get('likeCount', 0),
                    'Comment_Count': statistics.get('commentCount', 0), # 댓글 수도 추가함
                    'Published_At': snippet['publishedAt'],
                    'Thumbnail_URL': thumb_url,
                    'Video_ID': item['id']
                }
                all_videos.append(video_data)
                
        except Exception as e:
            print(f"Error [{cat_name}]: {e}")

    return pd.DataFrame(all_videos)

# --------------------------------------------------------
# 3. 메인 실행 및 파일 저장
# --------------------------------------------------------
if __name__ == "__main__":
    if API_KEY:
        # 10개 카테고리 * 20개 = 총 200개 목표
        df_result = get_videos_by_category(API_KEY, TARGET_CATEGORIES, target_count=20)
        
        if not df_result.empty:
            print("-" * 50)
            print(f"수집 완료! 총 {len(df_result)}개의 데이터를 확보했습니다.")
            
            # 파일명 설정
            save_filename = "youtube_top200_data.csv"
            
            # 코랩 가상 서버에 저장
            df_result.to_csv(save_filename, index=False, encoding='utf-8-sig')
            
            print(f"파일이 저장되었습니다: {os.path.abspath(save_filename)}")
            print("왼쪽 사이드바의 '폴더' 아이콘을 눌러 파일을 확인하고 다운로드하세요.")
            print("-" * 50)
            
            # 결과 일부 미리보기
            print(df_result[['Category_Name', 'Video_Title', 'View_Count']].head())
        else:
            print("데이터를 가져오지 못했습니다.")
