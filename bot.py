import os
import requests
import random
import json
import time
from groq import Groq

# 1. 환경 변수
webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
groq_key = os.environ.get("GROQ_API_KEY")

client_groq = Groq(api_key=groq_key)

# ---------------------------------------------------------
# 📡 1. 데이터 소스 (ESPN only - Real Data)
# ---------------------------------------------------------
def fetch_real_matches():
    print("📡 ESPN 데이터 검색 시작...")
    
    # 헤더 위장 (봇 차단 방지)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # NBA, EPL, 챔스, 라리가 순회
    endpoints = [
        ("basketball/nba", "🏀 NBA"),
        ("soccer/eng.1", "🇬🇧 EPL"),
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
                
                # 'pre'(경기전) 상태만 수집 (가상 데이터 절대 금지)
                if state == 'pre':
                    real_matches.append(f"{icon} {name}")
                    
        except Exception as e:
            print(f"⚠️ {icon} 검색 중 에러: {e}")
            continue

    return list(set(real_matches))

# ---------------------------------------------------------
# 🧠 2. AI 분석 (3개 국어)
# ---------------------------------------------------------
def get_ai_analysis(target):
    print(f"🧠 AI 분석 요청: {target}")
    model = "llama-3.3-70b-versatile"
    
    prompt = f"""
    Target: {target}
    Analyze this match for sports betting.
    
    Return the result in strict JSON format.
    {{
        "en": "Short prediction in English",
        "ko": "한국어 예측 (정배/역배 용어 사용)",
        "zh": "中文预测 (Simplified Chinese)"
    }}
    """
    
    try:
        response = client_groq.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
        )
        content = response.choices[0].message.content
        # JSON 문자열만 추출
        if "```" in content:
            content = content.split("```json")[-1].split("```")[0].strip()
        return json.loads(content)
    except Exception as e:
        print(f"❌ AI 분석 실패: {e}")
        return None

# ---------------------------------------------------------
# 🚀 3. 메인 실행 & 로그 확인
# ---------------------------------------------------------
def run():
    # 1. 경기 수집
    matches = fetch_real_matches()
    
    if not matches:
        print("💤 [결과] 현재 예정된 실제 경기가 없습니다. (종료)")
        return # 가상 경기 생성 안 함. 그냥 퇴근.

    print(f"✅ 발견된 경기 수: {len(matches)}개")
    target = random.choice(matches)
    
    # 2. 분석
    analysis = get_ai_analysis(target)
    if not analysis:
        print("❌ 분석 데이터가 비어있습니다. (종료)")
        return

    # 3. 디스코드 전송 (로그 집중)
    payload = {
        "username": "AI Sports Edge",
        "avatar_url": "[https://cdn-icons-png.flaticon.com/512/2585/2585184.png](https://cdn-icons-png.flaticon.com/512/2585/2585184.png)",
        "embeds": [
            {
                "title": f"🔥 Match Preview: {target}",
                "color": 3447003, # Blue
                "fields": [
                    {"name": "🇺🇸 English", "value": analysis.get('en', '-'), "inline": False},
                    {"name": "🇰🇷 한국어", "value": analysis.get('ko', '-'), "inline": False},
                    {"name": "🇨🇳 中文", "value": analysis.get('zh', '-'), "inline": False}
                ],
                "footer": {"text": "Real-time Data by ESPN"}
            }
        ]
    }

    if webhook_url:
        print(f"🚀 디스코드 전송 시작... (URL: {webhook_url[:10]}...)")
        try:
            res = requests.post(webhook_url, json=payload)
            
            # 👇 여기가 가장 중요합니다 (로그 확인용)
            print(f"📡 응답 상태 코드: {res.status_code}")
            
            if res.status_code == 204:
                print("✅ [성공] 디스코드 서버가 메시지를 정상적으로 수신했습니다.")
            elif res.status_code == 400:
                print(f"❌ [실패] 요청 형식이 잘못되었습니다. (Bad Request)")
                print(f"⚠️ 에러 내용: {res.text}")
            elif res.status_code == 404:
                print(f"❌ [실패] 웹훅 URL이 올바르지 않습니다. (Not Found)")
            else:
                print(f"❌ [실패] 알 수 없는 오류: {res.text}")
                
        except Exception as e:
            print(f"❌ [치명적 오류] 전송 중 예외 발생: {e}")
    else:
        print("⚠️ 웹훅 URL이 설정되지 않아 전송을 건너뜁니다.")
        print(json.dumps(analysis, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    run()
