import os
import requests
import random
import time
import re
from groq import Groq
from duckduckgo_search import DDGS # 👈 무료 검색 엔진 라이브러리

# 1. 환경 변수
webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
groq_key = os.environ.get("GROQ_API_KEY")

client_groq = Groq(api_key=groq_key)

SPORTS_CATEGORIES = {
    "⚽ SOCCER": [("soccer/eng.1", "🇬🇧 EPL"), ("soccer/uefa.champions", "🇪🇺 UCL")],
    "🏀 BASKETBALL": [("basketball/nba", "🇺🇸 NBA")],
    "⚾ BASEBALL": [("baseball/mlb", "🇺🇸 MLB")]
}

# ---------------------------------------------------------
# 📡 1. 경기 일정 수집 (ESPN)
# ---------------------------------------------------------
def fetch_matches_by_category(endpoints):
    headers = {"User-Agent": "Mozilla/5.0"}
    category_matches = []
    
    for sport_path, icon in endpoints:
        url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/scoreboard"
        try:
            res = requests.get(url, headers=headers, timeout=5)
            data = res.json()
            for event in data.get('events', []):
                state = event.get('status', {}).get('type', {}).get('state', '')
                if state == 'pre': 
                    name = event.get('name', 'Unknown')
                    category_matches.append(f"{icon} {name}")
        except:
            continue
            
    return list(set(category_matches))

# ---------------------------------------------------------
# 📰 2. 실시간 뉴스 검색 (The Game Changer)
# ---------------------------------------------------------
def fetch_latest_news(match_name):
    print(f"📰 [{match_name}] 관련 최신 뉴스 검색 중...")
    
    # 이모지 제거 및 검색 쿼리 최적화
    clean_name = re.sub(r'[^\w\s-]', '', match_name).strip()
    query = f"{clean_name} injury news preview"
    
    news_context = ""
    try:
        with DDGS() as ddgs:
            # 최근 1주일(timelimit='w') 뉴스 최대 3개 검색
            results = ddgs.text(query, max_results=3, timelimit='w')
            for idx, r in enumerate(results):
                title = r.get('title', '')
                body = r.get('body', '')
                news_context += f"News {idx+1}: [{title}] - {body}\n"
    except Exception as e:
        print(f"⚠️ 뉴스 검색 에러 (무시하고 진행): {e}")
        news_context = "최신 뉴스를 가져오지 못했습니다. 일반 지식으로 분석하세요."

    if not news_context.strip():
        news_context = "관련 뉴스가 없습니다."
        
    print("✅ 뉴스 스크랩 완료!")
    return news_context

# ---------------------------------------------------------
# 🧠 3. AI 분석 (뉴스 데이터 주입)
# ---------------------------------------------------------
def get_ai_analysis(target, category_name, news_data):
    print(f"🧠 AI 분석 중... (뉴스 데이터 반영)")
    model = "llama-3.3-70b-versatile"
    
    prompt = f"""
    Target Match: {target}
    Category: {category_name}
    Role: Professional Sports Betting Analyst.
    
    🚨 [CRITICAL DATA - READ THIS FIRST] 🚨
    Here are the latest news snippets regarding this match (Injuries, form, issues):
    {news_data}
    
    Task: 
    1. Base your analysis HEAVILY on the news provided above.
    2. Mention specific recent issues or injuries found in the news.
    3. Do NOT invent player names if they are not in the news.
    
    Format Structure:
    
    ===TITLE===
    (Match Title)
    
    ===KR===
    1. 📰 실시간 팩트: (제공된 뉴스 기반 최신 이슈/부상자 요약)
    2. 📉 양 팀 기세: (뉴스 분위기 반영)
    3. 🏃 승부처: (뉴스를 바탕으로 한 전술적 핵심)
    4. 😈 악마의 속삭임: (뉴스의 이면이나 숨은 배당 함정)
    5. 💰 최종 픽: (승패/언오버)
    
    ===EN===
    1. Live Fact Check: ...
    2. Team Momentum: ...
    3. Crucial Point: ...
    4. Devil's Whisper: ...
    5. Final Pick: ...
    
    ===ZH===
    1. 实时分析: ...
    2. 球队气势: ...
    3. 关键点: ...
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
# ✂️ 4. 데이터 가공
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
# 🚀 5. 메인 루프
# ---------------------------------------------------------
def run():
    print("🚀 [System] AI Sports Edge (RAG Edition) Started...")
    
    for category_name, endpoints in SPORTS_CATEGORIES.items():
        print(f"\n🔍 Searching for {category_name}...")
        
        matches = fetch_matches_by_category(endpoints)
        
        if not matches:
            print(f"   💤 {category_name}: 예정된 경기 없음.")
            continue 
            
        target = random.choice(matches)
        print(f"   ✅ Target Found: {target}")
        
        # 💡 [핵심] 뉴스 긁어오기
        news_data = fetch_latest_news(target)
        
        raw_text = get_ai_analysis(target, category_name, news_data)
        if not raw_text: continue
        
        data = parse_text_to_data(raw_text)
        
        embed = {
            "title": f"🏆 {category_name} Pick: {data.get('title')}",
            "color": 3447003,
            "fields": [
                {"name": "🇰🇷 한국어 (뉴스 기반 분석)", "value": data.get('kr', '-'), "inline": False},
                {"name": "🇺🇸 English Report", "value": data.get('en', '-'), "inline": False},
                {"name": "🇨🇳 中文报告", "value": data.get('zh', '-'), "inline": False}
            ],
            "footer": {"text": "Powered by ESPN & Live News Search • AI Sports Edge"}
        }
        
        payload = {"embeds": [embed]}
        
        if webhook_url:
            try:
                requests.post(webhook_url, json=payload)
                print(f"   🚀 {category_name} 리포트 전송 완료!")
            except Exception as e:
                print(f"   ❌ 전송 실패: {e}")
        
        time.sleep(5)

    print("\n🏁 [System] All Jobs Finished.")

if __name__ == "__main__":
    run()
