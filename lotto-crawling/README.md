# 🎰 로또 당첨 판매점 크롤러

동행복권 사이트(https://www.dhlottery.co.kr)에서 당첨 판매점 정보를 자동으로 수집하는 Python 크롤링 도구입니다.

## ✨ 주요 기능

- ✅ **회차별 조회**: 원하는 회차의 당첨 판매점 정보 수집
- ✅ **등수별 필터링**: 1등, 2등, 전체 등수별로 조회 가능
- ✅ **복권 종류별 조회**: 로또6/45, 연금복권720+, 스피또 시리즈
- ✅ **지역별 수집**: 전국 모든 지역의 판매점 정보 자동 수집
- ✅ **CSV 저장**: 수집된 데이터를 CSV 파일로 저장
- ✅ **상세 정보**: 판매점명, 주소, 전화번호, 좌표, 취급 복권 등

## 📦 설치 방법

### 1. Python 가상환경 생성 (권장)

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 또는
venv\Scripts\activate  # Windows
```

### 2. 필요한 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. Playwright 브라우저 설치

```bash
playwright install chromium
```

## 🚀 사용 방법

### 기본 사용법

```python
import asyncio
from lotto_crawler import LottoStoreCrawler

async def main():
    # 크롤러 생성
    crawler = LottoStoreCrawler(headless=True)
    
    try:
        # 브라우저 시작
        await crawler.start()
        
        # 판매점 정보 수집
        stores = await crawler.get_stores()
        
        # CSV 파일로 저장
        crawler.save_to_csv(stores, "lotto_stores.csv")
        
    finally:
        await crawler.close()

asyncio.run(main())
```

### 예제 1: 특정 회차의 1등 당첨 판매점만 수집

```python
async def example_1():
    crawler = LottoStoreCrawler(headless=False)  # 브라우저 보이도록 설정
    
    try:
        await crawler.start()
        
        # 로또6/45, 1206회, 1등만 선택
        await crawler.select_lottery_type("로또6/45")
        await crawler.select_round("1206")
        await crawler.select_rank("1등")
        
        # 데이터 수집 및 저장
        stores = await crawler.get_stores()
        crawler.save_to_csv(stores, "lotto_1st_prize_1206.csv")
        
    finally:
        await crawler.close()

asyncio.run(example_1())
```

### 예제 2: 모든 지역의 판매점 정보 수집

```python
async def example_2():
    crawler = LottoStoreCrawler(headless=True)
    
    try:
        await crawler.start()
        
        # 로또6/45 선택
        await crawler.select_lottery_type("로또6/45")
        await crawler.select_round("1206")
        await crawler.select_rank("전체")
        
        # 모든 지역 크롤링
        all_stores = await crawler.get_all_regions_stores()
        crawler.save_to_csv(all_stores, "lotto_all_regions.csv")
        
    finally:
        await crawler.close()

asyncio.run(example_2())
```

### 예제 3: 간단한 실행 (메인 스크립트)

제공된 메인 스크립트를 직접 실행할 수 있습니다:

```bash
python lotto_crawler.py
```

또는 간단한 예제 스크립트:

```bash
python simple_example.py
```

## 📊 출력 데이터 구조

CSV 파일에는 다음 정보가 포함됩니다:

| 컬럼명 | 설명 | 예시 |
|--------|------|------|
| 판매점ID | 고유 식별자 | 11110464 |
| 번호 | 목록 번호 | 23 |
| 판매점명 | 판매점 이름 | 꽃돼지복권방 |
| 등수 | 당첨 등수 | 1등, 2등 |
| 자동수동 | 자동/수동 여부 | 자동 |
| 지역 | 시/도 | 서울특별시 |
| 주소 | 상세 주소 | 서울 동대문구 장안동 361-4 |
| 전화번호 | 연락처 | 02-2248-6570 |
| 취급복권 | 취급하는 복권 종류 | 로또6/45, 스피또2000, 스피또1000 |
| 위도 | GPS 위도 | 37.566108 |
| 경도 | GPS 경도 | 127.068087 |
| 크롤링시간 | 수집 시간 | 2026-01-15 12:34:56 |

## ⚙️ 주요 메서드

### `LottoStoreCrawler` 클래스

#### `__init__(headless: bool = True)`
- **설명**: 크롤러 초기화
- **매개변수**: 
  - `headless`: 브라우저를 숨김 모드로 실행할지 여부 (True: 숨김, False: 보임)

#### `async start()`
- **설명**: 브라우저를 시작하고 페이지 로드

#### `async close()`
- **설명**: 브라우저 종료

#### `async select_lottery_type(lottery_type: str)`
- **설명**: 복권 종류 선택
- **매개변수**:
  - `lottery_type`: "로또6/45", "연금복권720+", "스피또2000", "스피또1000", "스피또500"

#### `async select_round(round_num: str)`
- **설명**: 회차 선택
- **매개변수**:
  - `round_num`: 회차 번호 (예: "1206")

#### `async select_rank(rank: str)`
- **설명**: 등수 선택
- **매개변수**:
  - `rank`: "전체", "1등", "2등"

#### `async get_stores() -> List[Dict]`
- **설명**: 현재 페이지의 판매점 정보 추출
- **반환**: 판매점 정보 딕셔너리 리스트

#### `async get_all_regions_stores() -> List[Dict]`
- **설명**: 모든 지역의 판매점 정보 수집
- **반환**: 전체 판매점 정보 딕셔너리 리스트

#### `save_to_csv(stores: List[Dict], filename: str = None)`
- **설명**: 판매점 정보를 CSV 파일로 저장
- **매개변수**:
  - `stores`: 판매점 정보 리스트
  - `filename`: 저장할 파일명 (기본값: lotto_stores_YYYYMMDD_HHMMSS.csv)

## 🔧 설정 옵션

### headless 모드
- `True`: 브라우저가 백그라운드에서 실행됩니다 (기본값)
- `False`: 브라우저 창이 보이면서 실행됩니다 (디버깅 시 유용)

## 📝 주의사항

1. **네트워크 속도**: 페이지 로딩 시간은 네트워크 상태에 따라 달라질 수 있습니다.
2. **대기 시간**: 각 필터 선택 후 1-2초의 대기 시간이 설정되어 있습니다. 너무 빠르게 동작하면 데이터 로드가 완료되지 않을 수 있습니다.
3. **모든 지역 크롤링**: `get_all_regions_stores()` 메서드는 모든 지역을 순회하므로 시간이 오래 걸립니다.
4. **웹사이트 정책**: 동행복권 웹사이트의 이용 약관을 준수하여 사용하시기 바랍니다.
5. **과도한 요청 금지**: 서버에 부담을 주지 않도록 적절한 간격으로 크롤링하세요.

## 🐛 문제 해결

### 1. Playwright 설치 오류
```bash
# Playwright 재설치
pip uninstall playwright
pip install playwright
playwright install chromium
```

### 2. 페이지 로딩 타임아웃
- `headless=False`로 설정하여 브라우저를 보면서 디버깅
- `asyncio.sleep()` 대기 시간을 늘려보세요

### 3. 데이터가 제대로 수집되지 않음
- 웹사이트 구조가 변경되었을 수 있습니다
- HTML 셀렉터를 확인하세요

## 📄 라이선스

이 프로젝트는 교육 및 연구 목적으로 제공됩니다. 상업적 용도로 사용 시 동행복권의 정책을 확인하세요.

## 🤝 기여

버그 리포트나 기능 제안은 이슈로 등록해주세요.

## 📞 문의

문제가 발생하면 이슈를 생성해주세요.

---

**⚠️ 면책 조항**: 이 도구는 교육 목적으로 제작되었습니다. 사용자는 관련 법률 및 웹사이트의 이용 약관을 준수할 책임이 있습니다.

