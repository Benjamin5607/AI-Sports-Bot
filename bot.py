import os
import requests
import random
import json
import time
from datetime import datetime
from groq import Groq

# 1. 환경 변수
webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
groq_key = os.environ.get("GROQ_API_KEY")

client_groq = Groq(api_key=groq_key)

# ---------------------------------------------------------
# 📡 데이터 소스: ESPN (The Global Standard)
# ---------------------------------------------------------
def fetch_espn_matches():
    # User-Agent를 최신 아이폰/크롬으로 위장
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "*/*"
    }
    
    # 인기 종목 API 엔드포인트
    leagues = [
        ("soccer/eng.1", "🇬🇧 EPL"), 
        ("soccer/esp.1", "🇪🇸 La Liga"),
        ("basketball/nba", "🇺🇸 NBA"),
        ("soccer/uefa.champions", "🇪🇺 UCL")
    ]
    
    match_list = []
    
    print("📡 ESPN 데이터 수신 중...")
    
    for endpoint, icon in leagues:
        url = f"https://site.api.espn.com/apis/site/v2/sports/{endpoint}/scoreboard"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            data = res.json()
            
            for event in data.get('events', []):
                state = event.get('status', {}).get('type', {}).get('state', '')
                # 'pre'(경기전) 상태인 것만 수집
                if state == 'pre':
                    name = event.get('name', 'Unknown Match')
                    match_list.append(f"{icon} {name}")
            
            time.sleep(1) # 차단 방지용 딜레이
            
        except Exception:
            continue

    return list(set(match_list)) # 중복 제거 후 반환

# ---------------------------------------------------------
# 🧠 AI 분석 (Trilingual Mode)
# ---------------------------------------------------------
def get_trilingual_analysis(target_match):
    # Llama 3는 언어 능력이 뛰어남
    model = "llama-3.3-70b-versatile"
    
    print(f"🧠 분석 시작: {target_match} (3개 국어)")

    prompt = f"""
    Target Match: {target_match}
    
    You are a global sports betting expert.
    Analyze this match and provide a prediction in strictly JSON format.
    
    Requirements for each language:
    1. English (en): Professional, analytical tone.
    2. Korean (ko): Natural predictions. Use terms like '정배'(favorite), '역배'(underdog). Don't sound translated.
    3. Chinese (zh): Standard Mandarin, concise sports commentary style. Use Simplified Chinese.

    JSON Structure:
    {{
        "en": "Prediction (Winner/Score) - Reason",
        "ko": "예측 (승패/점수) - 핵심 근거",
        "zh": "预测 (胜负/比分) - 分析理由",
        "pick_icon": "🔥" (Hot) or "🛡️" (Safe) or "💣" (Risky)
    }}
    
    Output ONLY valid JSON. No markdown.
    """
    
    try:
        response = client_groq.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
        )
        content = response.choices[0].message.content
        # 혹시 Markdown ```json 같은거 붙으면 떼어내기
        content = content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except Exception as e:
        print(f"❌ JSON 파싱 실패 또는 AI 에러: {e}")
        return None

# ---------------------------------------------------------
# 🚀 메인 실행
# ---------------------------------------------------------
def run():
    matches = fetch_espn_matches()
    
    if not matches:
        print("💤 현재 예정된 주요 경기가 없습니다.")
        return

    # 랜덤으로 하나 뽑기
    target_match = random.choice(matches)
    result = get_trilingual_analysis(target_match)

    if not result:
        return

    # 디스코드 전송 (Embed 꾸미기)
    payload = {
        "username": "AI Sports Edge Global",
        "avatar_url": "[https://cdn-icons-png.flaticon.com/512/2072/2072130.png](https://cdn-icons-png.flaticon.com/512/2072/2072130.png)", # 지구본 아이콘
        "embeds": [
            {
                "title": f"{target_match}",
                "description": f"**Global AI Prediction** {result.get('pick_icon', '⚽')}",
                "color": 3092790, # 청록색
                "fields": [
                    {
                        "name": "🇺🇸 English",
                        "value": result.get('en', 'Analysis Failed'),
                        "inline": False
                    },
                    {
                        "name": "🇰🇷 한국어",
                        "value": result.get('ko', '분석 실패'),
                        "inline": False
                    },
                    {
                        "name": "🇨🇳 中文",
                        "value": result.get('zh', '分析失败'),
                        "inline": False
                    }
                ],
                "footer": {
                    "text": "Powered by ESPN Data & Groq AI"
                }
            }
        ]
    }

    if webhook_url:
        requests.post(webhook_url, json=payload)
        print("✅ 3개 국어 리포트 전송 완료!")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    run()
