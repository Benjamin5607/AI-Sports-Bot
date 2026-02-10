import os
import requests
import random
from datetime import datetime
from groq import Groq

# 1. 환경 변수
webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
groq_key = os.environ.get("GROQ_API_KEY")

client_groq = Groq(api_key=groq_key)

# 2. 모델 자동 선택 (스마트함)
def get_best_model():
    try:
        models = client_groq.models.list()
        available_models = [m.id for m in models.data]
        priorities = ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"]
        for p in priorities:
            for m in available_models:
                if p in m: return m
        return "mixtral-8x7b-32768"
    except:
        return "mixtral-8x7b-32768"

# 3. 분석 대상 (랜덤 픽)
targets = [
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 EPL: Man City vs Liverpool",
    "🇪🇸 La Liga: Real Madrid vs Barcelona",
    "🇺🇸 NBA: Lakers vs Warriors",
    "⚾ MLB: Dodgers vs Yankees"
]
today_target = random.choice(targets)
date_str = datetime.now().strftime("%Y-%m-%d")

# 4. 분석 요청 (Embed용으로 짧게)
def get_ai_analysis():
    model = get_best_model()
    prompt = f"""
    분석 대상: {today_target}
    역할: 냉철한 스포츠 도박사 AI
    
    JSON 형식으로만 대답해. (Markdown 금지)
    {{
        "win_rate": "홈 45% / 무 30% / 원정 25% (예시임, 알아서 계산)",
        "pick": "홈팀 승리 (예시)",
        "reason": "핵심 근거 한 줄 (예시)"
    }}
    """
    try:
        response = client_groq.chat.completions.create(
            messages=[{"role": "user", "content": prompt, "response_format": {"type": "json_object"}}],
            model=model,
        )
        return response.choices[0].message.content
    except:
        # 혹시 JSON 모드 지원 안 하는 모델일 경우 대비
        return "데이터 분석 오류 발생"

# 5. 디스코드 전송 (간지나는 Embed 스타일)
def send_discord():
    if not webhook_url:
        print("⚠️ 웹훅 URL이 없습니다. 로그만 찍습니다.")
        return

    raw_data = get_ai_analysis()
    
    # 봇 프로필 & 메시지 설정
    payload = {
        "username": "AI Sports Edge",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/6062/6062646.png", # 미래지향적 로봇 아이콘
        "embeds": [
            {
                "title": f"📊 AI Match Prediction | {date_str}",
                "description": f"**Target:** {today_target}\n\n{raw_data}", # JSON 그대로 뿌려도 멋짐
                "color": 5814783, # 네온 블루
                "footer": {
                    "text": "Data powered by Groq Llama-3 • Not Financial Advice",
                    "icon_url": "https://cdn-icons-png.flaticon.com/512/25/25231.png" # 깃허브 아이콘
                }
            }
        ]
    }

    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 204:
            print("✅ 디스코드 전송 성공! (침대 해킹 완료)")
        else:
            print(f"❌ 전송 실패: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"❌ 에러: {e}")

if __name__ == "__main__":
    send_discord()
