import requests
import json
import os
from datetime import datetime, timedelta
from anthropic import Anthropic

# 초기화
client = Anthropic()

# Discord 웹훅
WEBHOOKS = {
    "bitcoin": os.environ.get("WEBHOOK_BITCOIN", ""),
    "stock": os.environ.get("WEBHOOK_STOCK", ""),
    "ai": os.environ.get("WEBHOOK_AI", ""),
    "economy": os.environ.get("WEBHOOK_ECONOMY", "")
}

# 📌 뉴스 히스토리 파일 (중복 방지)
NEWS_HISTORY_FILE = "sent_news_history.json"

# 히스토리 로드
def load_news_history():
    if os.path.exists(NEWS_HISTORY_FILE):
        with open(NEWS_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# 히스토리 저장
def save_news_history(history):
    with open(NEWS_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

# 뉴스가 이미 보냈는지 확인
def is_news_already_sent(title, history):
    return any(news["title"] == title for news in history)

# ✅ 수정: 과거 뉴스도 수집 (7일분)
def fetch_news(keyword, days=7):
    """
    days: 몇 일치의 뉴스를 수집할지 (기본 7일)
    """
    try:
        # ✅ 날짜 범위 확장 (과거 7일)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Google News API 또는 다른 뉴스 API
        # 예: NewsAPI 사용
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": keyword,
            "from": start_date.strftime("%Y-%m-%d"),
            "to": end_date.strftime("%Y-%m-%d"),
            "sortBy": "publishedAt",
            "language": "ko",
            "pageSize": 10
        }
        
        NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
        headers = {"Authorization": NEWS_API_KEY}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            articles = response.json().get("articles", [])
            return [
                {
                    "title": article["title"],
                    "url": article["url"],
                    "source": article["source"]["name"]
                }
                for article in articles
            ]
        return []
    except Exception as e:
        print(f"[ERROR] 뉴스 수집 실패: {str(e)}")
        return []

# ✅ 수정: 중복 제거 후 뉴스만 선택
def get_unique_news(keyword, days=7):
    """
    수집한 뉴스에서 이미 보낸 뉴스 제거
    """
    all_news = fetch_news(keyword, days=days)
    history = load_news_history()
    
    # 새로운 뉴스만 필터링
    new_news = [
        news for news in all_news 
        if not is_news_already_sent(news["title"], history)
    ]
    
    return new_news, history

# Claude로 뉴스 요약 생성
def generate_news_summary(news_list, topic):
    """
    뉴스 목록을 정리해서 원고 생성
    """
    if not news_list:
        return "오늘 새로운 뉴스가 없습니다."
    
    news_text = "\n".join([
        f"- [{news['source']}] {news['title']}"
        for news in news_list[:5]  # 상위 5개만
    ])
    
    prompt = f"""다음 {topic} 뉴스들을 정리해서 2줄 요약해줘:

{news_text}

형식: 
제목: [요약]
출처: [뉴스 출처]"""
    
    try:
        response = client.messages.create(
            model="claude-opus-4-1-20250805",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        return f"요약 실패: {str(e)}"

# Discord 발송
def send_to_discord(webhook_url, message, channel_name=""):
    try:
        payload = {"content": message}
        response = requests.post(webhook_url, json=payload, timeout=10)
        
        if response.status_code in [200, 204]:
            print(f"[SUCCESS] {channel_name} 채널 발송 완료")
            return True
        else:
            print(f"[ERROR] {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return False

# 메인 자동화
def run_automation(mode="news", topic="비트코인"):
    print(f"\n{'='*50}")
    print(f"[START] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} KST")
    print(f"{'='*50}\n")
    
    # 1️⃣ 뉴스 수집 (과거 7일)
    print(f"[STEP 1] '{topic}' 뉴스 수집 중 (과거 7일)...")
    new_news, history = get_unique_news(topic, days=7)
    
    if not new_news:
        print(f"[INFO] 새로운 뉴스 없음 (총 {len(history)}개 이미 보냄)")
        return
    
    print(f"[INFO] 새로운 뉴스 {len(new_news)}개 발견")
    
    # 2️⃣ 요약 생성
    print(f"\n[STEP 2] 뉴스 요약 생성 중...")
    summary = generate_news_summary(new_news, topic)
    
    # 3️⃣ Discord 발송
    print(f"\n[STEP 3] Discord 발송 중...")
    channel_map = {"비트코인": "bitcoin", "주식": "stock", "AI": "ai"}
    channel = channel_map.get(topic, "economy")
    webhook = WEBHOOKS.get(channel)
    
    if webhook and send_to_discord(webhook, summary, channel):
        # ✅ 히스토리 업데이트 (발송한 뉴스만 추가)
        for news in new_news:
            history.append({
                "title": news["title"],
                "sent_at": datetime.now().isoformat(),
                "source": news["source"]
            })
        save_news_history(history)
        print(f"[INFO] 히스토리 업데이트 (총 {len(history)}개)")
    
    print(f"\n{'='*50}\n")

if __name__ == "__main__":
    run_automation(mode="news", topic="비트코인")
