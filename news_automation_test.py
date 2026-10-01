import requests
import json
from datetime import datetime
from anthropic import Anthropic

# 초기화
client = Anthropic()

# Discord 웹훅 URL (GitHub Secrets에서 가져옴)
WEBHOOKS = {
    "bitcoin": "https://discordapp.com/api/webhooks/1554779417820266506/42KkDGX1fT-Xix8VXATl7-JgX2drI9XdvedwjZA_G3ZY3EtDMs-qfUN08om87-HbGOVM",
    "stock": "https://discordapp.com/api/webhooks/1554779586590547998/du7RqZt5byxmO6A0TbUqR8j0Dbd3hekxV4_u1T6mAJ6O8Og--SBjyv0Jrr6RSjsEAffG",
    "ai": "https://discordapp.com/api/webhooks/1554780010555117598/HKBDxIJUBcS0yQVaUvlJs9pnRqlIEYFg2JVJdZQMQeVbzvOIhKCeIZOOcSP8wFXCw5TQ",
    "economy": "https://discordapp.com/api/webhooks/1554779774877175859/QtU0Vzdp9GX1zOlJPDo1ocOtFOeV3C4gCTi3hnx2OK3RXfRN0C7-3xUNI0GjUmCvTBYA"
}

# 프롬프트 로드
def load_prompt(filename="cardnews_prompt.txt"):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"[ERROR] {filename} 파일을 찾을 수 없습니다")
        return ""

# Claude API로 원고 생성
def generate_cardnews(topic, mode="script"):
    """
    mode: 'news' (뉴스 헤드라인만) or 'script' (원고 생성)
    """
    prompt_template = load_prompt()
    
    if mode == "script":
        user_message = f"주제: {topic}\n\n7장 카드뉴스 원고를 생성해주세요."
    elif mode == "news":
        user_message = f"최신 {topic} 뉴스 3개의 헤드라인을 간단히 알려주세요."
    else:
        return None
    
    try:
        conversation_history = [
            {"role": "user", "content": prompt_template + "\n\n" + user_message}
        ]
        
        response = client.messages.create(
            model="claude-opus-4-1-20250805",
            max_tokens=2000,
            messages=conversation_history
        )
        
        return response.content[0].text
    except Exception as e:
        print(f"[ERROR] Claude API 호출 실패: {str(e)}")
        return None

# Discord 웹훅으로 메시지 발송
def send_to_discord(webhook_url, message, channel_name=""):
    """
    Discord 웹훅 호출 + 응답 로깅
    """
    try:
        payload = {"content": message}
        
        print(f"[DEBUG] 웹훅 호출 중: {channel_name}")
        print(f"[DEBUG] URL: {webhook_url[:50]}...") # URL 일부만 출력 (보안)
        
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=10
        )
        
        # ✅ 응답 로깅 (핵심 수정 부분)
        print(f"[INFO] Webhook response status: {response.status_code}")
        
        if response.status_code in [200, 204]:
            print(f"[SUCCESS] {channel_name} 채널에 메시지 전송 성공")
            return True
        else:
            print(f"[ERROR] Webhook failed - Status: {response.status_code}")
            print(f"[ERROR] Response body: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"[ERROR] Webhook timeout (10초 초과)")
        return False
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] 네트워크 연결 실패")
        return False
    except Exception as e:
        print(f"[ERROR] Webhook exception: {str(e)}")
        return False

# 메인 자동화 함수
def run_automation(mode="script", topic="비트코인"):
    """
    mode: 'script' (원고 생성) or 'news' (뉴스 헤드라인)
    """
    print(f"\n{'='*50}")
    print(f"[START] 자동화 시작 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} KST")
    print(f"[MODE] {mode.upper()}")
    print(f"{'='*50}\n")
    
    # 1. 원고 또는 뉴스 생성
    if mode == "script":
        print(f"[STEP 1] '{topic}' 관련 카드뉴스 원고 생성 중...")
        content = generate_cardnews(topic, mode="script")
        channel_map = {
            "비트코인": "bitcoin",
            "주식": "stock",
            "AI": "ai",
            "경제": "economy"
        }
        channel = channel_map.get(topic, "economy")
    elif mode == "news":
        print(f"[STEP 1] '{topic}' 최신 뉴스 수집 중...")
        content = generate_cardnews(topic, mode="news")
        # 뉴스 모드에서는 모든 채널에 전송
        channel = "economy"
    else:
        print("[ERROR] 잘못된 모드입니다")
        return
    
    if not content:
        print("[ERROR] 콘텐츠 생성 실패")
        return
    
    # 2. Discord 발송
    print(f"\n[STEP 2] Discord 웹훅 호출 중...\n")
    
    webhook_url = WEBHOOKS.get(channel)
    if not webhook_url:
        print(f"[ERROR] '{channel}' 채널의 웹훅을 찾을 수 없습니다")
        return
    
    success = send_to_discord(
        webhook_url,
        content,
        channel_name=channel
    )
    
    # 3. 결과 출력
    print(f"\n{'='*50}")
    if success:
        print(f"[SUCCESS] 자동화 완료 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} KST")
    else:
        print(f"[FAILED] 자동화 실패 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} KST")
    print(f"{'='*50}\n")

# 테스트 실행
if __name__ == "__main__":
    # 테스트 1: 원고 생성 모드
    run_automation(mode="script", topic="비트코인")
    
    # 테스트 2: 뉴스 모드 (선택사항)
    # run_automation(mode="news", topic="금융")
