import os
import requests
import random
import time
from groq import Groq

# 1. 환경 변수
webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
groq_key = os.environ.get("GROQ_API_KEY")

client_groq = Groq(api_key=groq_key)

# ---------------------------------------------------------
# 📡 1. 종목별 데이터 소스 정의
# ---------------------------------------------------------
SPORTS_CATEGORIES = {
    "⚽ SOCCER (Football)": [
        ("soccer/eng.1", "🇬🇧 EPL"),
        ("soccer/uefa.champions", "🇪🇺 UCL"),
        ("soccer/esp.1", "🇪🇸 La Liga"),
        ("soccer/ita.1", "🇮🇹 Serie A"),
        ("soccer/deu.1", "🇩🇪 Bundesliga")
    ],
    "🏀 BASKETBALL": [
        ("basketball/nba", "🇺🇸 NBA")
    ],
    "⚾ BASEBALL": [
        ("baseball/mlb", "🇺🇸 MLB")
    ]
}

def fetch_matches_by_category(endpoints):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    category_matches = []
    
    for sport_path, icon in endpoints:
        url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/scoreboard"
        try:
            res = requests.get(url, headers=headers, timeout=5)
            data = res.json()
            for event in data.get('events', []):
                state = event.get('status', {}).get('type', {}).get('state', '')
                name = event.get('name', 'Unknown')
                # 경기 전(pre) 상태만 수집
                if state == 'pre': 
                    category_matches.append(f"{icon} {name}")
        except:
            continue
            
    return list(set(category_matches))

# ---------------------------------------------------------
# 🧠 2. AI 분석 (안전한 텍스트 파싱)
# ---------------------------------------------------------
def get_ai_analysis(target, category_name):
    print(f"🧠 분석 요청 [{category_name}]: {target}")
    model = "llama-3.3-70b-versatile"
    
    prompt = f"""
    Target Match: {target}
    Category: {category_name}
    Role: Professional Sports Betting Analyst.
    
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
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ AI 에러: {e}")
        return None

# ---------------------------------------------------------
# ✂️ 3. 데이터 가공
# ---------------------------------------------------------
def parse_text_to_data(text):
    data = {}
    try:
        if "===TITLE===" in text:
            data['title'] = text.split("===TITLE===")[1].split("===KR===")[0].strip()
        else:
            data['title'] = "Match Analysis"
            
        if "===KR===" in text:
            data['kr'] = text.split("===KR===")[1].split("===EN===")[0].strip()
            
        if "===EN===" in text:
            data['en'] = text.split("===EN===")[1].split("===ZH===")[0].strip()
            
        if "===ZH===" in text:
            data['zh'] = text.split("===ZH===")[1].split("===END===")[0].strip()
            
        return data
    except:
        return {"title": "Error", "kr": text, "en": "-", "zh": "-"}

# ---------------------------------------------------------
# 🚀 4. 메인 실행 루프 (종목별 순회)
# ---------------------------------------------------------
def run():
    print("🚀 [System] Daily Sports Analysis Started...")
    
    # 각 종목별로 루프를 돕니다.
    for category_name, endpoints in SPORTS_CATEGORIES.items():
        print(f"\n🔍 Searching for {category_name}...")
        
        matches = fetch_matches_by_category(endpoints)
        
        if not matches:
            print(f"   💤 {category_name}: 예정된 경기 없음.")
            continue # 다음 종목으로 넘어감
            
        # 해당 종목에서 랜덤으로 1경기 선정
        target = random.choice(matches)
        print(f"   ✅ Target Found: {target}")
        
        # 분석 시작
        raw_text = get_ai_analysis(target, category_name)
        if not raw_text: continue
        
        data = parse_text_to_data(raw_text)
        
        # 디스코드 전송
        embed = {
            "title": f"🏆 {category_name} Pick: {data.get('title')}",
            "color": 3447003,
            "fields": [
                {"name": "🇰🇷 한국어 분석", "value": data.get('kr', '-'), "inline": False},
                {"name": "🇺🇸 English Report", "value": data.get('en', '-'), "inline": False},
                {"name": "🇨🇳 中文报告", "value": data.get('zh', '-'), "inline": False}
            ],
            "footer": {"text": "Powered by Groq Llama-3 • Not Financial Advice"}
        }
        
        payload = {"embeds": [embed]}
        
        if webhook_url:
            try:
                requests.post(webhook_url, json=payload)
                print(f"   🚀 {category_name} 리포트 전송 완료!")
            except Exception as e:
                print(f"   ❌ 전송 실패: {e}")
        
        # 다음 종목 분석 전, AI도 숨 좀 돌리고 봇 탐지 피하기 위해 5초 휴식
        print("   ⏳ Cooldown 5 seconds...")
        time.sleep(5)

    print("\n🏁 [System] All Jobs Finished.")

if __name__ == "__main__":
    run()
