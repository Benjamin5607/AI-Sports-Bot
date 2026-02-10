import os
import requests
import random
import json
import re # 👈 정규표현식(수술 도구) 추가
from groq import Groq

# 1. 환경 변수
webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
groq_key = os.environ.get("GROQ_API_KEY")

client_groq = Groq(api_key=groq_key)

# ---------------------------------------------------------
# 📡 1. 데이터 소스 (ESPN)
# ---------------------------------------------------------
def fetch_real_matches():
    print("📡 ESPN 데이터 검색 시작...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    endpoints = [
        ("soccer/eng.1", "🇬🇧 EPL"),
        ("basketball/nba", "🏀 NBA"),
        ("soccer/uefa.champions", "🇪🇺 UCL"),
        ("soccer/esp.1", "🇪🇸 La Liga")
    ]
    
    real_matches = []
    
    for sport, icon in endpoints:
        url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/scoreboard"
        try:
            res = requests.get(url, headers=headers, timeout=5)
            data = res.json()
            for event in data.get('events', []):
                state = event.get('status', {}).get('type', {}).get('state', '')
                name = event.get('name', 'Unknown')
                if state == 'pre': # 경기 전
                    real_matches.append(f"{icon} {name}")
        except:
            continue

    return list(set(real_matches))

# ---------------------------------------------------------
# 🧠 2. AI 분석 (JSON 수술 기능 탑재)
# ---------------------------------------------------------
def get_ai_analysis(target):
    print(f"🧠 AI 분석 요청: {target}")
    model = "llama-3.3-70b-versatile"
    
    # AI에게 배경지식 활용 강요
    prompt = f"""
    Analyze: {target}
    
    Role: Professional Sports Analyst.
    Task: Use your knowledge of these teams (recent form, H2H, key players) to predict the outcome.
    
    Output Format: JSON ONLY. No markdown, no intro.
    {{
        "en": "Prediction: [Team] wins / Score: [X-Y]. Reason: [Key Stat/Fact]",
        "ko": "예측: [팀] 승 / 스코어 [X-Y]. 이유: [최근 전적 등 근거]",
        "zh": "预测: [Team] 胜. 理由: [Analysis]"
    }}
    """
    
    try:
        response = client_groq.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
        )
        content = response.choices[0].message.content
        
        # 🚑 [긴급 수술] JSON만 발라내기 (Regex)
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
        else:
            # JSON을 못 찾았으면 강제로 만듦
            print("⚠️ JSON 형식이 아님. 원문 사용.")
            return {"en": content[:200], "ko": "데이터 파싱 실패 (원문 참조)", "zh": "-"}
            
    except Exception as e:
        print(f"❌ 분석 중 에러: {e}")
        # 에러 나도 죽지 말고 기본값 리턴
        return {
            "en": "Analysis unavailable",
            "ko": "현재 분석 데이터를 불러올 수 없습니다.",
            "zh": "暂无数据"
        }

# ---------------------------------------------------------
# 🚀 3. 메인 실행
# ---------------------------------------------------------
def run():
    matches = fetch_real_matches()
    
    if not matches:
        print("💤 경기 없음.")
        return

    print(f"✅ 발견된 경기 수: {len(matches)}개")
    target = random.choice(matches)
    
    analysis = get_ai_analysis(target)

    # 디스코드 전송
    payload = {
        "username": "AI Sports Edge",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/2585/2585184.png",
        "embeds": [
            {
                "title": f"🔥 Match Preview: {target}",
                "color": 3447003,
                "fields": [
                    {"name": "🇺🇸 English", "value": str(analysis.get('en', '-')), "inline": False},
                    {"name": "🇰🇷 한국어", "value": str(analysis.get('ko', '-')), "inline": False},
                    {"name": "🇨🇳 中文", "value": str(analysis.get('zh', '-')), "inline": False}
                ],
                "footer": {"text": "Powered by Groq AI"}
            }
        ]
    }

    if webhook_url:
        print(f"🚀 디스코드 전송 시도...")
        try:
            res = requests.post(webhook_url, json=payload)
            if res.status_code == 204:
                print("✅ [성공] 전송 완료!")
            else:
                print(f"❌ [실패] 코드: {res.status_code}, 메시지: {res.text}")
        except Exception as e:
            print(f"❌ 전송 에러: {e}")
    else:
        print(json.dumps(analysis, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    run()
