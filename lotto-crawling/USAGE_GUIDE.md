# 📖 로또 크롤러 사용 가이드

이 문서는 로또 당첨 판매점 크롤러를 처음 사용하는 분들을 위한 상세 가이드입니다.

## 🎯 목차

1. [설치하기](#1-설치하기)
2. [첫 실행](#2-첫-실행)
3. [다양한 사용 예제](#3-다양한-사용-예제)
4. [문제 해결](#4-문제-해결)
5. [팁과 트릭](#5-팁과-트릭)

---

## 1. 설치하기

### Step 1: Python 설치 확인

Python 3.8 이상이 필요합니다.

```bash
python --version
# 또는
python3 --version
```

### Step 2: 프로젝트 다운로드

```bash
git clone <repository-url>
cd lotto-crawling
```

### Step 3: 가상환경 생성 (권장)

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

가상환경이 활성화되면 터미널 프롬프트 앞에 `(venv)`가 표시됩니다.

### Step 4: 패키지 설치

```bash
pip install -r requirements.txt
```

### Step 5: Playwright 브라우저 설치

```bash
playwright install chromium
```

설치가 완료되면 준비 완료! 🎉

---

## 2. 첫 실행

### 가장 간단한 방법

터미널에서 다음 명령어를 입력하세요:

```bash
python simple_example.py
```

그러면 다음과 같은 메뉴가 나타납니다:

```
실행할 예제를 선택하세요:
1. 기본 크롤링 (로또 6/45, 1206회, 전체 등수)
2. 1등 당첨 판매점만 수집
3. 모든 지역 판매점 수집 (시간 오래 걸림)

번호를 입력하세요 (1-3):
```

**처음 사용하시는 분은 `1`번을 선택하세요!**

### 결과 확인

크롤링이 완료되면 프로젝트 폴더에 `lotto_stores_simple.csv` 파일이 생성됩니다.
Excel이나 Google Sheets에서 열어서 확인할 수 있습니다.

---

## 3. 다양한 사용 예제

### 예제 A: 특정 회차의 1등 당첨 판매점만 수집

```python
import asyncio
from lotto_crawler import LottoStoreCrawler

async def get_first_prize():
    crawler = LottoStoreCrawler(headless=False)
    
    try:
        await crawler.start()
        
        # 로또 6/45, 1205회, 1등만
        await crawler.select_lottery_type("로또6/45")
        await crawler.select_round("1205")
        await crawler.select_rank("1등")
        
        stores = await crawler.get_stores()
        crawler.save_to_csv(stores, "1등_당첨판매점_1205회.csv")
        
        print(f"✅ 1등 당첨 판매점 {len(stores)}곳을 찾았습니다!")
        
    finally:
        await crawler.close()

asyncio.run(get_first_prize())
```

### 예제 B: 연금복권 당첨 판매점 수집

```python
async def get_pension_lottery():
    crawler = LottoStoreCrawler(headless=True)
    
    try:
        await crawler.start()
        
        # 연금복권 720+ 선택
        await crawler.select_lottery_type("연금복권720+")
        await crawler.select_round("500")  # 원하는 회차
        await crawler.select_rank("전체")
        
        stores = await crawler.get_stores()
        crawler.save_to_csv(stores, "연금복권_당첨판매점.csv")
        
    finally:
        await crawler.close()

asyncio.run(get_pension_lottery())
```

### 예제 C: 여러 회차를 한 번에 수집

```python
async def get_multiple_rounds():
    crawler = LottoStoreCrawler(headless=True)
    all_stores = []
    
    try:
        await crawler.start()
        await crawler.select_lottery_type("로또6/45")
        await crawler.select_rank("1등")
        
        # 1200회부터 1206회까지
        for round_num in range(1200, 1207):
            print(f"📥 {round_num}회 수집 중...")
            await crawler.select_round(str(round_num))
            stores = await crawler.get_stores()
            
            # 회차 정보 추가
            for store in stores:
                store['회차'] = round_num
            
            all_stores.extend(stores)
        
        crawler.save_to_csv(all_stores, "1등_1200-1206회_통합.csv")
        print(f"✅ 총 {len(all_stores)}곳의 판매점 정보 수집 완료!")
        
    finally:
        await crawler.close()

asyncio.run(get_multiple_rounds())
```

### 예제 D: 특정 지역만 필터링

```python
async def get_seoul_stores():
    crawler = LottoStoreCrawler(headless=False)
    
    try:
        await crawler.start()
        await crawler.select_lottery_type("로또6/45")
        await crawler.select_round("1206")
        await crawler.select_rank("전체")
        
        # 모든 판매점 수집
        all_stores = await crawler.get_stores()
        
        # 서울 지역만 필터링
        seoul_stores = [
            store for store in all_stores 
            if '서울' in store['지역'] or '서울' in store['주소']
        ]
        
        crawler.save_to_csv(seoul_stores, "서울_당첨판매점.csv")
        print(f"✅ 서울 지역 판매점 {len(seoul_stores)}곳 수집 완료!")
        
    finally:
        await crawler.close()

asyncio.run(get_seoul_stores())
```

---

## 4. 문제 해결

### 문제 1: "playwright not found" 오류

**해결책:**
```bash
pip install playwright
playwright install chromium
```

### 문제 2: 타임아웃 오류

```python
# 대기 시간을 늘려보세요
await asyncio.sleep(3)  # 기본 1초 → 3초로 증가
```

또는 스크립트 내부의 `wait_for_selector` 타임아웃을 늘리세요:
```python
await self.page.wait_for_selector('.store-list', state='visible', timeout=30000)
```

### 문제 3: 브라우저가 열리지 않음

**해결책:**
`headless=False`로 설정하여 브라우저를 보면서 디버깅:
```python
crawler = LottoStoreCrawler(headless=False)
```

### 문제 4: CSV 파일이 Excel에서 한글이 깨짐

현재 스크립트는 `utf-8-sig` 인코딩을 사용하므로 Excel에서 정상적으로 열립니다.
만약 여전히 깨진다면:

1. Excel에서 "데이터" → "텍스트 나누기" 사용
2. 파일을 메모장에서 열고 "다른 이름으로 저장" → 인코딩: UTF-8 BOM 선택

### 문제 5: 데이터가 하나도 수집되지 않음

**확인사항:**
1. 인터넷 연결 확인
2. 동행복권 사이트가 정상 작동하는지 확인
3. 웹사이트 구조가 변경되었을 수 있음 → HTML 셀렉터 확인

---

## 5. 팁과 트릭

### 💡 Tip 1: 브라우저 보면서 실행하기

처음 사용할 때는 `headless=False`로 설정하면 무슨 일이 일어나는지 볼 수 있습니다:

```python
crawler = LottoStoreCrawler(headless=False)
```

### 💡 Tip 2: 대기 시간 조절

네트워크가 느리면 대기 시간을 늘리세요:

```python
# lotto_crawler.py 파일의 asyncio.sleep(1) 부분을
await asyncio.sleep(2)  # 또는 3
```

### 💡 Tip 3: 특정 조건의 판매점만 필터링

수집 후 Python으로 필터링:

```python
# 자동 선택으로 1등 당첨된 판매점만
auto_first_prize = [
    store for store in stores 
    if store['등수'] == '1등' and store['자동수동'] == '자동'
]
```

### 💡 Tip 4: 판매점 정보를 JSON으로도 저장

```python
import json

with open('lotto_stores.json', 'w', encoding='utf-8') as f:
    json.dump(stores, f, ensure_ascii=False, indent=2)
```

### 💡 Tip 5: 진행 상황 표시줄 추가

`tqdm` 패키지 설치:
```bash
pip install tqdm
```

사용 예제:
```python
from tqdm import tqdm

for round_num in tqdm(range(1200, 1207), desc="회차 수집 중"):
    await crawler.select_round(str(round_num))
    stores = await crawler.get_stores()
    all_stores.extend(stores)
```

### 💡 Tip 6: 스케줄링으로 자동 실행

매주 토요일 자동으로 실행하려면 `schedule` 패키지 사용:

```bash
pip install schedule
```

```python
import schedule
import time

def job():
    asyncio.run(simple_crawl())

# 매주 토요일 오후 9시에 실행
schedule.every().saturday.at("21:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## 🎓 더 알아보기

### 고급 사용법

복잡한 분석을 위해 Pandas를 사용할 수 있습니다:

```python
import pandas as pd

# CSV 읽기
df = pd.read_csv('lotto_stores.csv')

# 지역별 1등 당첨 횟수
first_prize_by_region = df[df['등수'] == '1등'].groupby('지역').size()
print(first_prize_by_region)

# 가장 많이 당첨된 판매점
top_stores = df['판매점명'].value_counts().head(10)
print(top_stores)
```

### 데이터 시각화

```bash
pip install matplotlib seaborn
```

```python
import matplotlib.pyplot as plt
import seaborn as sns

# 한글 폰트 설정
plt.rcParams['font.family'] = 'AppleGothic'  # macOS
# 또는
# plt.rcParams['font.family'] = 'Malgun Gothic'  # Windows

# 지역별 당첨 판매점 수
df['지역'].value_counts().plot(kind='bar')
plt.title('지역별 당첨 판매점 수')
plt.xlabel('지역')
plt.ylabel('판매점 수')
plt.tight_layout()
plt.savefig('region_analysis.png')
plt.show()
```

---

## 📞 도움이 필요하신가요?

- 버그 발견: GitHub Issues에 등록
- 기능 제안: Pull Request 환영
- 질문: Discussions 활용

**Happy Crawling! 🎰🎉**

