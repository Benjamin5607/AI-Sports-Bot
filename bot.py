import os
import requests
import random
import time
import json
from datetime import datetime, timedelta
from groq import Groq

# 1. 환경 변수
webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
groq_key = os.environ.get("GROQ_API_KEY")

client_groq = Groq(api_key=groq_key)

# ---------------------------------------------------------
# 🕵️‍♂️ 스텔스 모듈 (인간 위장)
# ---------------------------------------------------------
def get_headers():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
    ]
    return {
        "User-Agent": random.choice(user_agents),
        "Referer": "https://www.google.com/",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
    }

def human_sleep():
    # 2초에서 5초 사이 랜덤하게 쉬기 (기계적 패턴 방지)
    sleep_time = random.uniform(2, 5)
    print(f"🕵️‍♂️ 인간인 척 {sleep_time:.1f}초 대기 중...")
    time.sleep(sleep_time)

# ---------------------------------------------------------
# 📡 데이터 소스 1: ESPN (Hidden API - 글로벌 표준)
# ---------------------------------------------------------
def fetch_espn_matches():
    print("📡 [Source 1] ESPN 접속 시도...")
    human_sleep()
    
    # ESPN은 종목별로 주소가 다름. 오늘은 축구(EPL)와 농구(NBA) 스캔
    sources = [
        ("soccer/eng.1", "EPL"),          # 프리미어리그
        ("soccer/esp.1", "La Liga"),      # 라리가
        ("basketball/nba", "NBA"),        # NBA
        ("soccer/uefa.champions", "UCL")  # 챔스
    ]
    
    matches = []
    
    for endpoint, league_name in sources:
        url = f"https://site.api.espn.com/apis/site/v2/sports/{endpoint}/scoreboard"
        try:
            res = requests.get(url, headers=get_headers())
            data = res.json()
            
            for event in data.get('events', []):
                name = event.get('name', 'Unknown')
                status = event.get('status', {}).get('type', {}).get('state', '')
                
                # 'pre'는 경기 전, 'in'은 경기 중. (종료된 건 제외)
                if status in ['pre', 'in']:
                    matches.append(f"[{league_name}] {name}")
            
            human_sleep() # 리그 하나 긁고 잠깐 쉬기
            
        except Exception:
            continue # 에러 나면 다음 리그로 패스

    return matches

# ---------------------------------------------------------
# 📡 데이터 소스 2: 네이버 스포츠 (국내 최적화)
# ---------------------------------------------------------
def fetch_naver_matches():
    print("📡 [Source 2] 네이버 스포츠 접속 시도...")
    human_sleep()
    
    kst_now = datetime.utcnow() + timedelta(hours=9)
    date_str = kst_now.strftime("%Y%m%d")
    
    url = f"https://sports.news.naver.com/wfootball/schedule/list.json?date={date_str}"
    
    matches = []
    try:
        res = requests.get(url, headers=get_headers())
        data = res.json()
        
        target_leagues = ["프리미어리그", "라리가", "분데스리가", "챔피언스리그", "NBA"]
        
        for game in data.get('scheduleList', []):
            league = game.get('categoryName', '')
            home = game.get('homeTeamName', '')
            away = game.get('awayTeamName', '')
            state = game.get('state', '') # 'BEFORE', 'LIVE' 등
            
            # 진행 전이거나 라이브인 빅리그 경기만
            if any(tl in league for tl in target_leagues) and state in ['BEFORE', 'LIVE']:
                matches.append(f"[{league}] {home} vs {away}")
                
    except Exception as e:
        print(f"❌ 네이버 실패: {e}")
        
    return matches

# ---------------------------------------------------------
# 🧠 중앙 처리 장치
# ---------------------------------------------------------
def get_best_match():
    # 1. ESPN 먼저 털기
    match_pool = fetch_espn_matches()
    
    # 2. 만약 ESPN이 부실하면 네이버 털기
    if not match_pool:
        print("⚠️ ESPN 데이터 없음, 네이버로 우회합니다.")
        match_pool = fetch_naver_matches()
    else:
        # 네이버도 긁어서 합치면 더 좋음 (데이터 풍부)
        naver_pool = fetch_naver_matches()
        match_pool.extend(naver_pool)
    
    # 중복 제거 및 랜덤 픽
    match_pool = list(set(match_pool))
    
    if not match_pool:
        return None
        
    print(f"📦 수집된 경기 목록: {len(match_pool)}개 발견")
    return random.choice(match_pool)

def get_ai_analysis(target_match):
    model = "llama-3.3-70b-versatile"
    
    prompt = f"""
    당신은 스포츠 도박사가 가장 신뢰하는 AI 분석관입니다.
    
    [Target Match]
    {target_match}
    
    위 경기는 곧 시작하거나 진행 중인 실제 경기입니다.
    인터넷 커뮤니티(디시인사이드, 펨코 등)의 고수 느낌으로 분석글을 작성하세요.
    (반말 사용, 거친 말투 허용, 이모지 많이 사용)

    1. 📊 **전력 팩트체크**
       - 양 팀의 최근 분위기 3줄 요약

    2. 👿 **악마의 속삭임 (Key Insight)**
       - 배당률이나 라인업 변수 등 날카로운 지적

    3. 💰 **최종 픽 (Pick)**
       - [승/패] 또는 [언더/오버] 딱 정해서 말해.
       - "형 믿고 따라와" 멘트 추가.
    """
    
    try:
        response = client_groq.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"분석 엔진 과부하: {e}"

# ---------------------------------------------------------
# 🚀 메인 실행
# ---------------------------------------------------------
if __name__ == "__main__":
    print("🚀 [System] AI Sports Edge 가동 (Stealth Mode: ON)")
    
    match = get_best_match()
    
    if match:
        print(f"🎯 타겟 확정: {match}")
        analysis = get_ai_analysis(match)
        
        payload = {
            "username": "AI Sports Edge",
            "avatar_url": "https://cdn-icons-png.flaticon.com/512/1698/1698535.png", # 해커/봇 느낌 아이콘
            "embeds": [
                {
                    "title": f"⚡ LIVE DATA: {match}",
                    "description": analysis,
                    "color": 10181046, # 퍼플 (신비로운 색)
                    "footer": {
                        "text": "Sources: ESPN, Naver • Secured by Proxy"
                    }
                }
            ]
        }
        
        if webhook_url:
            requests.post(webhook_url, json=payload)
            print("✅ 디스코드 전송 완료")
        else:
            print(analysis)
    else:
        print("💤 현재 진행 예정인 빅매치가 없습니다. 스텔스 모드 종료.")
