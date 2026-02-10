import os
import requests
import random
import json
import re
from groq import Groq

# 1. 환경 변수
webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
groq_key = os.environ.get("GROQ_API_KEY")

client_groq = Groq(api_key=groq_key)

# ---------------------------------------------------------
# 📡 1. 데이터 소스 (ESPN - Real Data)
# ---------------------------------------------------------
def fetch_real_matches():
    print("📡 ESPN 데이터 검색 시작...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # 분석할 가치가 있는 빅리그만 선정
    endpoints = [
        ("soccer/eng.1", "🇬🇧 EPL"),
        ("basketball/nba", "🏀 NBA"),
        ("soccer/uefa.champions", "🇪🇺 UCL"),
        ("soccer/esp.1", "🇪🇸 La Liga"),
        ("soccer/ita.1", "🇮🇹 Serie A")
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
                # 경기 전(pre) 상태인 것만
                if state == 'pre': 
                    real_matches.append(f"{icon} {name}")
        except:
            continue

    return list(set(real_matches))

# ---------------------------------------------------------
# 🧠 2. AI 분석 (5대 핵심 요소 탑재)
# ---------------------------------------------------------
def get_ai_analysis(target):
    print(f"🧠 심층 분석 요청: {target}")
    model = "llama-3.3-70b-versatile"
    
    # 파트너님이 요청한 5가지 섹션을 프롬프트에 강력하게 주입
    prompt = f"""
    Target Match: {target}
    Role: Senior Sports Betting Analyst.
    
    Task: Analyze this match based on 5 key sections.
    Language: Korean (Professional & Analytical tone).
    
    Output Format: JSON ONLY (No markdown).
    
    JSON Structure:
    {{
        "match_title": "{target}",
        "fact_check": "양 팀의 현재 순위, 부상자 현황, 전술적 상성 등 객관적 전력 비교 (2줄 요약)",
        "recent_form": "양 팀의 최근 5경기 흐름 및 분위기 분석 (상승세/하락세 위주)",
        "key_player": "이 경기를 지배할 핵심 선수 1명과 그 이유",
        "devils_whisper": "대중이 놓치고 있는 위험 요소나 배당의 함정 (역배 가능성 등 날카로운 지적)",
        "final_pick": "승/패 또는 언더/오버 (확률 포함)",
        "risk_rating": "⭐⭐⭐"
    }}
    """
    
    try:
        response = client_groq.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=0.7 # 창의성 약간 추가 (악마의 속삭임을 위해)
        )
        content = response.choices[0].message.content
        
        # JSON 수술 (Regex)
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        else:
            raise ValueError("JSON Not Found")
            
    except Exception as e:
        print(f"❌ 분석 중 에러: {e}")
        return None

# ---------------------------------------------------------
# 🚀 3. 메인 실행 & 디스코드 전송
# ---------------------------------------------------------
def run():
    matches = fetch_real_matches()
    
    if not matches:
        print("💤 경기 없음.")
        return

    print(f"✅ 발견된 경기 수: {len(matches)}개")
    target = random.choice(matches)
    
    data = get_ai_analysis(target)
    
    if not data:
        print("❌ 데이터 생성 실패")
        return

    # 디스코드 Embed 디자인 (섹션별 아이콘 적용)
    embed = {
        "title": f"🏆 {data.get('match_title', target)}",
        "description": f"**Risk Level:** `{data.get('risk_rating', '⭐⭐⭐')}`",
        "color": 2123412, # Dark Gray (진지한 느낌)
        "fields": [
            {
                "name": "1️⃣ 전력 팩트 체크 (Power Check)",
                "value": data.get('fact_check', '-'),
                "inline": False
            },
            {
                "name": "2️⃣ 최근 5경기 흐름 (Recent Form)",
                "value": data.get('recent_form', '-'),
                "inline": False
            },
            {
                "name": "3️⃣ 주목해야 할 선수 (Key Player)",
                "value": f"**🏃 {data.get('key_player', '-')}**",
                "inline": False
            },
            {
                "name": "4️⃣ 😈 악마의 속삭임 (Devil's Whisper)",
                "value": f"*{data.get('devils_whisper', '-')}*",
                "inline": False
            },
            {
                "name": "5️⃣ 💰 최종 픽 (Final Verdict)",
                "value": f"```fix\n{data.get('final_pick', '-')} \n```",
                "inline": False
            }
        ],
        "footer": {
            "text": "Analysis by AI Sports Edge • Invest Responsibly",
            "icon_url": "https://cdn-icons-png.flaticon.com/512/4712/4712009.png"
        }
    }

    payload = {
        "username": "AI Sports Edge",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/2585/2585184.png",
        "embeds": [embed]
    }

    if webhook_url:
        print(f"🚀 디스코드 전송 시도...")
        try:
            res = requests.post(webhook_url, json=payload)
            if res.status_code == 204:
                print("✅ [성공] 프리미엄 리포트 전송 완료!")
            else:
                print(f"❌ [실패] 코드: {res.status_code}, 메시지: {res.text}")
        except Exception as e:
            print(f"❌ 전송 에러: {e}")
    else:
        # 웹훅 없을 때 로그 확인용
        print(json.dumps(data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    run()
