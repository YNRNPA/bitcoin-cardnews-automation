#!/usr/bin/env python3
import os
import requests
from datetime import datetime
import anthropic

DISCORD_WEBHOOKS = {
    "bitcoin": "https://discordapp.com/api/webhooks/1554779417820266506/42KkDGX1fT-Xix8VXATl7-JgX2drI9XdvedwjZA_G3ZY3EtDMs-qfUN08om87-HbGOVM",
    "stock": "https://discordapp.com/api/webhooks/1554779586590547998/du7RqZt5byxmO6A0TbUqR8j0Dbd3hekxV4_u1T6mAJ6O8Og--SBjyv0Jrr6RSjsEAffG",
    "ai": "https://discordapp.com/api/webhooks/1554780010555117598/HKBDxIJUBcS0yQVaUvlJs9pnRqlIEYFg2JVJdZQMQeVbzvOIhKCeIZOOcSP8wFXCw5TQ",
    "economy": "https://discordapp.com/api/webhooks/1554779774877175859/QtU0Vzdp9GX1zOlJPDo1ocOtFOeV3C4gCTi3hnx2OK3RXfRN0C7-3xUNI0GjUmCvTBYA"
}

def send_message(webhook_url, title, content):
    payload = {
        "embeds": [{
            "title": title,
            "description": content,
            "color": 1957147,
            "timestamp": datetime.now().isoformat(),
            "footer": {"text": "자동화된 뉴스"}
        }]
    }
    try:
        requests.post(webhook_url, json=payload)
        print(f"✅ {title} 전송 완료")
    except Exception as e:
        print(f"❌ 오류: {e}")

if __name__ == "__main__":
    print("🤖 자동화 시작")
    test_msg = "✅ GitHub Actions 테스트 성공!\n자동화가 정상 작동합니다."
    
    for name, url in DISCORD_WEBHOOKS.items():
        send_message(url, f"[테스트] {name}", test_msg)
    
    print("✅ 모두 완료!")
