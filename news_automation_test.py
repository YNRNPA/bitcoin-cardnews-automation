name: 비트코인 뉴스 자동화

on:
  schedule:
    # 매일 10시 (한국 시간)
    - cron: '0 1 * * *'
    # 매일 16시 (한국 시간)
    - cron: '0 7 * * *'
    # 매일 22시 (한국 시간)
    - cron: '0 13 * * *'
  workflow_dispatch:  # 수동 실행도 가능

jobs:
  news-automation:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Python 설정
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: 필요한 라이브러리 설치
        run: |
          pip install requests anthropic
      
      - name: 자동화 스크립트 실행
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: python news_automation_test.py
