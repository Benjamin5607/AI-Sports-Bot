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
client = tweepy.Client(
    consumer_key=consumer_key, consumer_secret=consumer_secret,
    access_token=access_token, access_token_secret=access_token_secret
)
groq_client = Groq(api_key=groq_key)

# 3. (임시) 분석할 경기 데이터 - 나중엔 크롤링으로 대체
# 오늘은 일단 AI가 '가상의 빅매치'나 '일반적인 스포츠 격언'을 분석하게 유도
targets = [
    "Premier League: Man City vs Liverpool",
    "NBA: Lakers vs Warriors",
    "Champions League: Real Madrid vs Bayern Munich"
]
today_target = random.choice(targets)
date_str = datetime.now().strftime("%Y-%m-%d")

# 4. Groq에게 분석 요청
prompt = f"""
오늘은 {date_str}이다.
주제: {today_target} 경기 승부 예측.

당신은 '냉철한 AI 스포츠 분석가'이다.
다음 조건에 맞춰 트위터(X) 포스팅을 작성하라:
1. 한국어로 작성.
2. 양 팀의 가상 데이터(최근 승률 등)를 기반으로 승리 확률(%)을 계산해서 제시하라. (그럴듯하게)
3. 말투는 "분석 결과:", "승률:", "~로 예측됨." 처럼 건조하고 짧게.
4. 이모지(⚽, 📊, 🤖) 적절히 사용.
5. 해시태그 필수: #스포츠분석 #AI픽 #SportsEdge #토토
6. 전체 길이는 공백 포함 200자 이내.

절대 서론(안녕하세요 등)을 쓰지 말고 바로 본론으로 들어가라.
"""

response = groq_client.chat.completions.create(
    messages=[{"role": "user", "content": prompt}],
    model="llama3-70b-8192",
)
tweet_content = response.choices[0].message.content

# 5. 트윗 발사
try:
    client.create_tweet(text=tweet_content)
    print("✅ 트윗 전송 성공!")
    print(tweet_content)
except Exception as e:
    print(f"❌ 전송 실패: {e}")
