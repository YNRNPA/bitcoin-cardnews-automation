#!/usr/bin/env python3
"""
비트코인/금융 뉴스 자동화 엔진
"""

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

DUMMY_NEWS = {
    "bitcoin": [{"title": "비트코인 현물 ETF, 9월 신규 유입 사상 최대", "description": "미국의 현물 비트코인 ETF가 9월에만 약 150억 달러의 자금을 유입받으면서 기관투자자들의 관심이 집중되고 있습니다.", "category": "📱비트코인"}],
    "stock": [{"title": "삼성전자, AI 반도체 투자 확대", "description": "삼성전자가 2025년까지 생성형 AI 반도체에 50조원을 투자하기로 결정했습니다.", "category": "📈주식"}],
    "ai": [{"title": "OpenAI, 새로운 O3 모델 공개 예정", "description": "OpenAI가 10월 중 차세대 추론 모델 O3를 공개할 예정입니다.", "category": "🤖AI"}],
    "economy": [{"title": "한국은행, 기준금리 인하 검토", "description": "한국은행 금통위가 10월 회의에서 기준금리 인하를 검토할 것으로 예상됩니다.", "category": "💰경제"}]
}

def send_to_discord(webhook_url: str, content: str, news_title: str) -> bool:
    payload = {
        "embeds": [
            {
                "title": news_title,
                "description": content,
                "color": 1957147,
                "timestamp": datetime.now().isoformat(),
                "footer": {"text": "Bitcoin Insight | 자동화된 뉴스 분석"}
            }
        ]
    }
    try:
        response = requests.post(webhook_url, json=payload)
        return response.status_code == 204
    except Exception as e:
        print(f"❌ Discord 발행 실패: {e}")
        return False

def run_automation():
    print("\n" + "="*60)
    print("🤖 뉴스 자동화 엔진 시작")
    print(f"⏰ 현재 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    test_content = "✅ GitHub Actions 테스트 성공!\n\n이 메시지가 보이면 자동화가 정상 작동합니다."
    
    for category, webhook_url in DISCORD_WEBHOOKS.items():
        print(f"\n🔄 {category.upper()} 채널에 전송 중...")
        success = send_to_discord(webhook_url, test_content, f"[테스트] {category} 자동화")
        if success:
            print(f"✅ {category} 전송 완료!")
        else:
            print(f"❌ {category} 전송 실패!")

if __name__ == "__main__":
    run_automation()
