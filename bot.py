import os
import requests
import random
from datetime import datetime
from groq import Groq

# 1. 환경 변수
webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
groq_key = os.environ.get("GROQ_API_KEY")

client_groq = Groq(api_key=groq_key)

# 2. 모델 선택 (똑똑한 놈 필수)
def get_best_model():
    try:
        models = client_groq.models.list()
        # Llama 3 70B 모델이 가장 말을 잘함
        target_models = ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile"]
        for m in models.data:
            if m.id in target_models: return m.id
        return "mixtral-8x7b-32768"
    except:
        return "mixtral-8x7b-32768"

# 3. 분석 대상 (가상의 매치업)
targets = [
    "⚽ EPL: Man City vs Arsenal",
    "🏀 NBA: Lakers vs Warriors",
    "⚾ MLB: Dodgers vs Yankees",
    "⚽ UCL: Real Madrid vs Bayern"
]
today_target = random.choice(targets)
date_str = datetime.now().strftime("%Y-%m-%d")

# 4. 분석 요청 (프롬프트 대폭 강화)
def get_ai_analysis():
    model = get_best_model()
    
    prompt = f"""
    당신은 전설적인 스포츠 분석가입니다.
    대상: {today_target} ({date_str})
    
    다음 4가지 항목을 포함하여 전문적인 분석 리포트를 작성하세요.
    (한국어로 작성, Markdown 문법 활용하여 가독성 높일 것)

    1. 📊 **최근 전적 및 흐름 (Recent Form)**
       - 두 팀의 최근 5경기 결과 요약 (가상의 데이터 기반)
       - 홈/원정 경기력 차이 분석

    2. 👥 **예상 라인업 & 매치업 (Key Matchups)**
       - 주요 부상자 및 결장 예상 선수
       - 승부를 가를 핵심 선수(Key Player) 1명씩 선정 및 비교

    3. 📝 **경기 양상 예측 (Game Flow)**
       - 초반 흐름과 승부처 예상
       - 전술적 포인트 (예: 빠른 템포, 수비 집중 등)

    4. 🎯 **최종 데이터 예측 (Final Verdict)**
       - 승리 확률: 홈 OO% / 원정 OO%
       - 추천 픽: (승패 또는 언더/오버)
       - 한 줄 요약: (냉철한 결론)

    ※ 주의: 너무 길지 않게 핵심만 요약해서 전체 1000자 이내로 작성.
    """
    
    try:
        response = client_groq.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ 분석 생성 실패: {str(e)}"

# 5. 디스코드 전송
def send_discord():
    analysis_result = get_ai_analysis()
    
    payload = {
        "username": "AI Sports Edge",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/6062/6062646.png",
        "embeds": [
            {
                "title": f"📑 프리미엄 분석 리포트 | {today_target}",
                "description": analysis_result,
                "color": 3447003, # 고급진 네이비 블루
                "footer": {
                    "text": f"📅 {date_str} • Powered by Groq Llama-3 (High-End Mode)"
                }
            }
        ]
    }

    if webhook_url:
        requests.post(webhook_url, json=payload)
        print("✅ 프리미엄 리포트 전송 완료")
    else:
        print(analysis_result)

if __name__ == "__main__":
    send_discord()
