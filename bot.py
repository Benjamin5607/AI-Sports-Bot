import tweepy
import os
import random
from datetime import datetime
from groq import Groq

# 1. 환경 변수 로드
consumer_key = os.environ.get("TWITTER_API_KEY")
consumer_secret = os.environ.get("TWITTER_API_SECRET")
access_token = os.environ.get("TWITTER_ACCESS_TOKEN")
access_token_secret = os.environ.get("TWITTER_ACCESS_SECRET")
groq_key = os.environ.get("GROQ_API_KEY")

# 2. 클라이언트 연결
client_x = tweepy.Client(
    consumer_key=consumer_key, consumer_secret=consumer_secret,
    access_token=access_token, access_token_secret=access_token_secret
)
client_groq = Groq(api_key=groq_key)

# 🔄 [New] 알바생 자동 호출 함수 (지금 할 일 없는 모델 소환)
def get_best_model():
    try:
        models = client_groq.models.list()
        available_models = [m.id for m in models.data]
        
        # 1순위: Llama 3.x 계열 (가장 똑똑함)
        for m in available_models:
            if "llama-3.3" in m: return m
        for m in available_models:
            if "llama-3.1" in m: return m
        for m in available_models:
            if "llama3" in m: return m
            
        # 2순위: Mixtral (가성비 좋음)
        for m in available_models:
            if "mixtral" in m: return m
            
        # 3순위: 아무나 나와 (오디오 모델인 whisper만 제외하고)
        for m in available_models:
            if "whisper" not in m: return m
            
        return "mixtral-8x7b-32768" # 정 안되면 이 친구로 고정
    except Exception as e:
        print(f"모델 리스트 못 가져옴: {e}")
        return "mixtral-8x7b-32768" # 에러나면 안전빵으로

# 3. 타겟 설정 (나중에 크롤링으로 대체)
targets = [
    "EPL: Man City vs Liverpool",
    "NBA: Lakers vs Warriors",
    "Champions League: Real Madrid vs Bayern",
    "MLB: Dodgers vs Yankees"
]
today_target = random.choice(targets)
date_str = datetime.now().strftime("%Y-%m-%d")

# 4. 분석 및 트윗 생성
def generate_tweet():
    current_model = get_best_model() # 여기서 알바생 호출
    print(f"🤖 오늘 근무할 모델: {current_model}")

    prompt = f"""
    상황: {date_str}, {today_target} 경기.
    역할: 냉소적인 스포츠 도박사 AI.
    
    트위터 포스팅 작성 (조건):
    1. 한국어.
    2. 승률(%)을 데이터 기반인 척 계산해서 제시.
    3. 이모지(⚽, 📉) 사용.
    4. 해시태그: #스포츠분석 #AI픽 #SportsEdge
    5. 잡담 금지. 200자 이내.
    """

    response = client_groq.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=current_model, # 자동 선택된 모델 투입
    )
    return response.choices[0].message.content

# 5. 실행
try:
    tweet_text = generate_tweet()
    response = client_x.create_tweet(text=tweet_text)
    print(f"✅ 트윗 전송 성공! (ID: {response.data['id']})")
    print(f"내용: {tweet_text}")
except Exception as e:
    print(f"❌ 에러 발생: {e}")
