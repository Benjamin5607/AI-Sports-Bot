import os
import requests
import random
import re
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
                if state == 'pre': 
                    real_matches.append(f"{icon} {name}")
        except:
            continue

    return list(set(real_matches))

# ---------------------------------------------------------
# 🧠 2. AI 분석 (구분자 방식 - 외계어 방지)
# ---------------------------------------------------------
def get_ai_analysis(target):
    print(f"🧠 정밀 분석 요청: {target}")
    model = "llama-3.3-70b-versatile"
    
    # JSON 강요를 없애고, 텍스트 덩어리로 받음
    prompt = f"""
    Target Match: {target}
    Role: Professional Sports Analyst.
    
    Write a report in 3 languages using the EXACT format below.
    Do not use JSON. Just write the text.
    
    Format Structure:
    
    ===TITLE===
    (Write the Match Title here)
    
    ===KR===
    (한국어로 작성)
    1. 📊 전력 팩트: (2줄 요약)
    2. 📉 최근 흐름: (5경기 분위기)
    3. 🏃 키 플레이어: (선수명 - 이유)
    4. 😈 악마의 속삭임: (배당 함정/변수 분석)
    5. 💰 최종 픽: (승패/언오버)
    
    ===EN===
    (Write in English)
    1. Power Check: ...
    2. Recent Form: ...
    3. Key Player: ...
    4. Devil's Whisper: ...
    5. Final Pick: ...
    
    ===ZH===
    (Write in Simplified Chinese)
    1. 实力分析: ...
    2. 近期状态: ...
    3. 关键球员: ...
    4. 恶魔低语: ...
    5. 最终预测: ...
    
    ===END===
    """
    
    try:
        response = client_groq.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=0.3 # 👈 온도를 낮춰서 헛소리 방지
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ 생성 에러: {e}")
        return None

# ---------------------------------------------------------
# ✂️ 3. 데이터 가공 (가위질)
# ---------------------------------------------------------
def parse_text_to_data(text):
    data = {}
    
    # 구분자로 텍스트 쪼개기
    try:
        if "===TITLE===" in text:
            data['title'] = text.split("===TITLE===")[1].split("===KR===")[0].strip()
        else:
            data['title'] = "Unknown Match"
            
        if "===KR===" in text:
            data['kr'] = text.split("===KR===")[1].split("===EN===")[0].strip()
            
        if "===EN===" in text:
            data['en'] = text.split("===EN===")[1].split("===ZH===")[0].strip()
            
        if "===ZH===" in text:
            data['zh'] = text.split("===ZH===")[1].split("===END===")[0].strip()
            
        # 픽(Pick)만 따로 추출해서 강조 (정규표현식)
        # 한국어 파트에서 '최종 픽:' 뒤에 있는 내용을 잡음
        pick_match = re.search(r'5\. 💰 최종 픽:(.*)', data.get('kr', ''))
        if pick_match:
            data['pick'] = pick_match.group(1).strip()
        else:
            data['pick'] = "See details"
            
    except Exception as e:
        print(f"❌ 파싱 에러: {e}")
        # 에러나면 통으로라도 보여주기 위해
        data['kr'] = text
        data['en'] = "Parsing Error"
        data['zh'] = "Parsing Error"
        data['pick'] = "Check Report"
        
    return data

# ---------------------------------------------------------
# 🚀 4. 메인 실행
# ---------------------------------------------------------
def run():
    matches = fetch_real_matches()
    
    if not matches:
        print("💤 경기 없음.")
        return

    print(f"✅ 발견된 경기 수: {len(matches)}개")
    target = random.choice(matches)
    
    # 1. AI가 글 쓰기
    raw_text = get_ai_analysis(target)
    if not raw_text: return
    
    # 2. 파이썬이 가위질하기
    data = parse_text_to_data(raw_text)

    # 3. 디스코드 포장
    embed = {
        "title": f"🏆 {data.get('title')}",
        "description": f"**🤖 AI Analyst's Pick:**\n```fix\n{data.get('pick')}\n```",
        "color": 3447003,
        "fields": [
            {
                "name": "🇰🇷 한국어 분석",
                "value": data.get('kr', '-'),
                "inline": False
            },
            {
                "name": "🇺🇸 English Report",
                "value": data.get('en', '-'),
                "inline": False
            },
            {
                "name": "🇨🇳 中文报告",
                "value": data.get('zh', '-'),
                "inline": False
            }
        ],
        "footer": {
            "text": "Powered by Groq Llama-3 • Invest Responsibly",
            "icon_url": "https://cdn-icons-png.flaticon.com/512/10605/10605937.png"
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
                print("✅ [성공] 전송 완료!")
            else:
                print(f"❌ [실패] 코드: {res.status_code}, 메시지: {res.text}")
        except Exception as e:
            print(f"❌ 전송 에러: {e}")
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    run()
