#!/usr/bin/env python3
"""
카드뉴스 원고 자동화
- 10시, 16시: 분야별 원고 1개씩 (후킹문구 3개 + 7장 원고 + 캡션)
- 22시: 분야별 뉴스 헤드라인만 전달
"""
import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from urllib.parse import quote

KST = timezone(timedelta(hours=9))

TOPICS = {
    "bitcoin": {"name": "📱비트코인", "query": "비트코인 OR 가상자산 OR 이더리움", "webhook": "WEBHOOK_BITCOIN"},
    "stock":   {"name": "📈주식",     "query": "코스피 OR 미국증시 OR 나스닥 OR 삼성전자", "webhook": "WEBHOOK_STOCK"},
    "ai":      {"name": "🤖AI",       "query": "인공지능 OR 생성형AI OR 오픈AI OR 엔비디아", "webhook": "WEBHOOK_AI"},
    "economy": {"name": "💰경제",     "query": "기준금리 OR 환율 OR 물가 OR 부동산", "webhook": "WEBHOOK_ECONOMY"},
}

MODEL = "claude-sonnet-5-5"


# ---------- 뉴스 수집 (구글 뉴스 RSS, 무료) ----------
def fetch_news(query, hours=6, limit=10):
    for window in (f"{hours}h", "24h"):
        url = f"https://news.google.com/rss/search?q={quote(query)}+when:{window}&hl=ko&gl=KR&ceid=KR:ko"
        try:
            r = requests.get(url, timeout=15)
            root = ET.fromstring(r.content)
        except Exception as e:
            print(f"뉴스 수집 실패: {e}")
            continue
        items = []
        for it in root.iter("item"):
            title = it.findtext("title", "")
            source = it.findtext("source", "")
            if source and title.endswith(f" - {source}"):
                title = title[: -len(source) - 3]
            items.append({"title": title, "link": it.findtext("link", ""), "source": source})
            if len(items) >= limit:
                break
        if items:
            return items
    return []


# ---------- 원고 생성 ----------
PROMPT = """너는 구독자 10만 경제·재테크 인스타그램 카드뉴스 에디터야.
아래 [{topic}] 최신 뉴스 중 사람들이 가장 반응할 만한 것 1개를 골라 카드뉴스 원고를 써줘.

[뉴스 목록]
{news}

[후킹 문구 스타일 — 가장 중요]
- 의심, 반전, 도발형 어그로. 15자 이내.
- 예시 느낌: 반감기? 글쎄.. / 삼성전자, 아직도 믿어? / 금리 내렸는데 이자는 그대로? / 이거 모르면 또 물립니다
- 문구 안에 큰따옴표(")는 쓰지 말 것.
- 단, 뉴스에 없는 사실을 지어내거나 무조건 오른다 같은 수익 보장 표현은 금지. 어그로는 말투로만.
- 3개는 서로 다른 각도로 (의심형 / 반전형 / 경고형).

[원고 규칙]
- 초등학생도 이해하는 쉬운 말. 전문용어는 쉬운 말로 풀기.
- 7장. 각 장: title 15자 이내, body 2줄 이내(줄당 20자 이내, 줄바꿈은 \\n).
- 1장 title은 후킹 문구 A와 동일, body는 궁금증 유발 한 줄.
- 7장은 한 줄 요약 + 저장/팔로우 유도.
- caption: 2문장 이내. hashtags: 5개.

반드시 save_cardnews 도구로 결과를 저장해."""


CARDNEWS_TOOL = {
    "name": "save_cardnews",
    "description": "완성된 카드뉴스 원고를 저장한다.",
    "input_schema": {
        "type": "object",
        "properties": {
            "news_index": {"type": "integer", "description": "고른 뉴스 번호"},
            "topic_title": {"type": "string", "description": "원고 주제 한 줄"},
            "hooks": {"type": "array", "items": {"type": "string"}, "minItems": 3, "maxItems": 3,
                      "description": "후킹 문구 3개 (의심형, 반전형, 경고형)"},
            "slides": {
                "type": "array", "minItems": 7, "maxItems": 7,
                "items": {
                    "type": "object",
                    "properties": {"title": {"type": "string"}, "body": {"type": "string"}},
                    "required": ["title", "body"],
                },
            },
            "caption": {"type": "string"},
            "hashtags": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["news_index", "topic_title", "hooks", "slides", "caption", "hashtags"],
    },
}


def write_script(topic_name, news, retries=2):
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    news_text = "\n".join(f"{i}. {n['title']} ({n['source']})" for i, n in enumerate(news))
    last_err = None
    for attempt in range(retries + 1):
        try:
            msg = client.messages.create(
                model=MODEL,
                max_tokens=2500,
                tools=[CARDNEWS_TOOL],
                tool_choice={"type": "tool", "name": "save_cardnews"},
                messages=[{"role": "user", "content": PROMPT.format(topic=topic_name, news=news_text)}],
            )
            for block in msg.content:
                if block.type == "tool_use":
                    data = block.input
                    if len(data.get("slides", [])) >= 7 and len(data.get("hooks", [])) >= 3:
                        return data
            last_err = f"형식 불완전 (stop_reason={msg.stop_reason})"
        except Exception as e:
            last_err = e
        print(f"  재시도 {attempt + 1}: {last_err}")
    raise RuntimeError(last_err)


def format_script(data, news):
    lines = []
    labels = ["A", "B", "C"]
    lines.append("🎣 **후킹 문구 (택1)**")
    for label, hook in zip(labels, data["hooks"]):
        lines.append(f"{label}. {hook}")
    lines.append("")
    for i, s in enumerate(data["slides"], 1):
        body = s["body"].replace("\n", "\n　　 ")
        lines.append(f"**{i}장** | {s['title']}\n　　 {body}")
    lines.append("")
    lines.append(f"✍️ **캡션:** {data['caption']}")
    lines.append(" ".join(data["hashtags"]))
    idx = data.get("news_index", 0)
    if 0 <= idx < len(news):
        lines.append(f"\n🔗 원문: [{news[idx]['source']}]({news[idx]['link']})")
    return "\n".join(lines)


def format_headlines(news):
    return "\n".join(f"{i}. [{n['title']}]({n['link']}) · {n['source']}" for i, n in enumerate(news[:5], 1))


# ---------- 디스코드 발송 ----------
def send(webhook_url, title, body):
    payload = {"embeds": [{
        "title": title[:250],
        "description": body[:4000],
        "color": 0x1E3A8A,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }]}
    r = requests.post(webhook_url, json=payload, timeout=15)
    print(f"  디스코드 전송: {r.status_code}")


# ---------- 실행 ----------
def main():
    now = datetime.now(KST)
    mode = os.environ.get("MODE") or ("news" if now.hour >= 20 else "script")
    print(f"⏰ {now:%Y-%m-%d %H:%M} KST / 모드: {mode}")

    for key, t in TOPICS.items():
        webhook = os.environ.get(t["webhook"])
        if not webhook:
            print(f"⚠️ {t['webhook']} 시크릿 없음 → {t['name']} 건너뜀")
            continue

        news = fetch_news(t["query"], hours=6 if mode == "script" else 12)
        if not news:
            print(f"⚠️ {t['name']} 뉴스 없음")
            continue

        try:
            if mode == "news":
                send(webhook, f"🌙 {t['name']} 오늘 저녁 뉴스", format_headlines(news))
            else:
                data = write_script(t["name"], news)
                send(webhook, f"📌 {t['name']} | {data['topic_title']}", format_script(data, news))
            print(f"✅ {t['name']} 완료")
        except Exception as e:
            print(f"❌ {t['name']} 오류: {e}")


if __name__ == "__main__":
    main()
