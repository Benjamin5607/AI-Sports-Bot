import os
import requests
import random
import time
import re
import urllib.parse
import xml.etree.ElementTree as ET # 👈 구글 뉴스 파싱용 (기본 내장)
from groq import Groq

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
# 📰 2. 구글 뉴스 RSS 해킹 (막힘 없는 팩트 수집)
# ---------------------------------------------------------
def fetch_google_news(match_name):
    print(f"📰 [{match_name}] 구글 뉴스 RSS 스캔 중...")
    
    # 검색어 정제 (예: "🇬🇧 EPL Manchester United vs West Ham" -> "Manchester United West Ham")
    clean_name = re.sub(r'[^\w\s]', ' ', match_name).replace('EPL', '').replace('NBA', '').replace('MLB', '').strip()
    
    # 검색 쿼리: 팀 이름 + 부상(injury) 또는 프리뷰(preview)
    query = urllib.parse.quote(f"{clean_name} injury OR preview OR news")
    
    # 구글 뉴스 RSS 주소 (영어 기사가 팩트가 가장 정확함)
    url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    
    news_context = ""
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        root = ET.fromstring(res.text)
        
        # 상위 4개 기사 제목과 발행일 가져오기
        items = root.findall('.//item')[:4]
        for idx, item in enumerate(items):
            title = item.find('title').text
            pub_date = item.find('pubDate').text
            news_context += f"- [{pub_date}] {title}\n"
            
    except Exception as e:
        print(f"⚠️ 뉴스 검색 실패: {e}")
        
    if not news_context.strip():
        news_context = "관련 최신 뉴스를 찾을 수 없습니다. 일반 지식과 전력 위주로 분석하세요."
        
    print(f"✅ 수집된 뉴스 데이터:\n{news_context}")
    return news_context

# ---------------------------------------------------------
# 🧠 3. AI 분석 (실시간 팩트 주입)
# ---------------------------------------------------------
def get_ai_analysis(target, category_name, news_data):
    print(f"🧠 AI 분석 시작...")
    model = "llama-3.3-70b-versatile"
    
    prompt = f"""
    Target Match: {target}
    Category: {category_name}
    Role: Professional Sports Betting Analyst.
    
    🚨 [LIVE NEWS DATA] 🚨
    Read these latest news headlines regarding the match:
    {news_data}
    
    Task: 
    1. Base your analysis HEAVILY on the news provided above.
    2. Explicitly mention injuries, manager quotes, or team form found in the headlines.
    3. Do NOT invent information not present in the news or your established knowledge base.
    
    Format Structure:
    
    ===TITLE===
    (Match Title)
    
    ===KR===
    1. 📰 실시간 팩트: (뉴스 헤드라인을 바탕으로 한 최신 이슈 요약)
    2. 📉 양 팀 기세: (상승세/하락세 분석)
    3. 🏃 승부처: (뉴스를 반영한 전술적 핵심)
    4. 😈 악마의 속삭임: (배당 함정이나 숨겨진 리스크)
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
    print("🚀 [System] AI Sports Edge (Google News RAG Edition) Started...")
    
    for category_name, endpoints in SPORTS_CATEGORIES.items():
        print(f"\n🔍 Searching for {category_name}...")
        
        matches = fetch_matches_by_category(endpoints)
        
        if not matches:
            print(f"   💤 {category_name}: 예정된 경기 없음.")
            continue 
            
        target = random.choice(matches)
        print(f"   ✅ Target Found: {target}")
        
        # 💡 구글 뉴스 RSS 스캔
        news_data = fetch_google_news(target)
        
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
            "footer": {"text": "Powered by ESPN & Google News RSS • AI Sports Edge"}
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
