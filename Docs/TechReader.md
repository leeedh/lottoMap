# 📑 로또 명당 서비스 기능명세서

---

## 1. 개발 우선순위

(쉬운 기능 → 핵심 기능 → 중간 난이도 → 어려운 기능)

1. **쉬운 기능** ✅

   * 공통 레이아웃 (사이드바)
   * UI 컴포넌트 구축 (StoreCard 등)
   * 모바일 반응형 레이아웃

2. **핵심 기능** ✅ (현재 구현 중)

   * 지도 기반 판매점 표시 (Kakao Map API)
   * 판매점 필터 (복권 종류: 로또 6/45, 연금복권)
   * 판매점 상세 정보 (인포윈도우, 카드 확장)
   * 랭킹 기능 (전국/지역별 Top 판매점)
   * 자동 데이터 업데이트 (크롤링 + 지오코딩 + DB 반영) - 🔄 향후 구현

3. **중간 난이도 기능** (향후 구현)

   * 히트맵 시각화
   * "오늘의 추천 명당" 기능

4. **어려운 기능** (향후 구현)

   * 사용자 후기/제보 시스템
   * 광고/스폰서십 노출

---

## 2. 프론트엔드 기능명세서

### 현재 구현 상태

**기술 스택**: React 18 + Vite (SPA), TypeScript, Tailwind CSS, Kakao Map API  
**데이터 소스**: 목업 데이터 (`constants.ts`의 `MOCK_STORES`)

### 공통 레이아웃

* **파일 위치**:
  * `App.tsx` (메인 앱 컴포넌트)
  * `components/Sidebar.tsx` (사이드바)
  * `components/MapContainer.tsx` (지도 컨테이너)
  * `components/StoreCard.tsx` (판매점 카드)

* **구성**:
  * **App**: 메인 레이아웃 (사이드바 + 지도 영역), 필터 상태 관리
  * **Sidebar**: 
    * 탭 (지도 내 명당 / 전체 랭킹)
    * 필터 (복권 종류: 로또 6/45, 연금복권)
    * 지역 필터 (랭킹 탭: 시/도, 시/군/구 드롭다운)
    * 판매점 리스트 (StoreCard 컴포넌트)
  * **MapContainer**: Kakao Map API 기반 지도, 마커 표시, 인포윈도우
  * **StoreCard**: 판매점 정보 카드 (당첨 통계, 이력 표시)

---

### 메인 페이지 (단일 페이지 애플리케이션)

* **파일**: `App.tsx`

* **구성 요소**:

  * **지도 뷰** (`components/MapContainer.tsx`) → Kakao Map SDK
    * 커스텀 마커 (로또/연금복권 구분)
    * 인포윈도우 (판매점 상세 정보)
    * 지도 범위 제한 (한국 영토 내)
    
  * **사이드바** (`components/Sidebar.tsx`)
    * **지도 내 명당 탭**: 현재 지도 영역 내 표시된 판매점 리스트
      * 복권 종류 필터 (로또 6/45, 연금복권)
    * **전체 랭킹 탭**: 전국/지역별 Top 판매점 리스트
      * 지역 필터 (시/도, 시/군/구)
      * 1등 당첨 횟수 기준 정렬

* **데이터 소스**

  * 목업 데이터: `constants.ts`의 `MOCK_STORES`
  * 타입 정의: `types.ts` (Store, WinRecord, WinStats 등)

* **테스트 항목**

  * ✅ 지도 로딩 시 마커 표시 정상 여부
  * ✅ 복권 종류 필터 동작 여부
  * ✅ 마커 클릭 → 인포윈도우 표시
  * ✅ 카드 클릭 → 지도 이동 및 선택 표시
  * ✅ 모바일 반응형 동작 (사이드바 드로어)

---

### 판매점 상세 정보

* **구현 위치**: 
  * 지도 마커 클릭 → 인포윈도우 (`components/MapContainer.tsx`)
  * 사이드바 카드 클릭 → 카드 확장 (`components/StoreCard.tsx`)

* **구성 요소**:

  * 판매점 정보 (이름, 주소)
  * 당첨 통계 (로또 1등, 로또 2등, 연금복권 횟수)
  * 최근 당첨 이력 (회차, 등수, 방법, 날짜)

* **데이터 소스**

  * 목업 데이터: `Store.history` (WinRecord 배열)

* **테스트 항목**

  * ✅ 인포윈도우 내용 정확성
  * ✅ 카드 확장/축소 동작
  * ✅ 당첨 이력 최신순 정렬

---

### 랭킹 기능

* **구현 위치**: `components/Sidebar.tsx` (전체 랭킹 탭)

* **구성 요소**:

  * 지역 필터 (시/도, 시/군/구 드롭다운)
  * 랭킹 리스트 (1등 당첨 횟수 기준 정렬)
  * 순위 표시 (1~3위 메달 아이콘, 4위 이상 숫자)

* **데이터 소스**

  * 목업 데이터: `MOCK_STORES` 필터링 및 정렬

* **테스트 항목**

  * ✅ 지역 필터 동작 정상 여부
  * ✅ 랭킹 정렬 정확성 (1등 당첨 횟수 기준)
  * ✅ 카드 클릭 → 지도 이동 및 선택

---

### 모바일 반응형

* **구현 위치**: `App.tsx` (모바일 UI 오버레이)

* **구성 요소**:

  * 모바일 헤더 (로고, 커피 후원 버튼)
  * 플로팅 필터 칩 (로또 6/45, 연금복권)
  * 하단 플로팅 버튼 (명당 리스트 보기)
  * 사이드바 드로어 (모바일에서 전체 화면)

* **테스트 항목**

  * ✅ 모바일 화면에서 사이드바 드로어 동작
  * ✅ 필터 칩 동작
  * ✅ 하단 버튼 동작

---

## 3. 백엔드 기능명세서

### 현재 상태

**백엔드 API 없음** - 현재는 목업 데이터를 직접 사용하는 프론트엔드만 구현됨

### 향후 구현 계획

### API 정의 (Next.js Route Handlers 또는 별도 백엔드)

* **파일 위치** (예정):

  * `app/api/stores/route.ts`
  * `app/api/stores/[id]/route.ts`
  * `app/api/rankings/route.ts`

* **엔드포인트** (예정):

  * `GET /api/stores`
    * 요청: `bbox`, `q`, `rank`
    * 응답: 판매점 리스트 (좌표 포함)
  * `GET /api/stores/:id`
    * 요청: 판매점 ID
    * 응답: 판매점 상세 정보
  * `GET /api/stores/:id/history`  (App Router 기준 예: `/api/stores/[id]/history`)
    * 요청: 판매점 ID
    * 응답: 회차별 당첨 이력
  * `GET /api/rankings`
    * 요청: scope(city|province|national), lotteryType(LOTTO|PENSION), rank, limit
    * 응답: 랭킹 리스트

> 참고: `rank`의 허용 범위는 `lotteryType`에 따라 달라집니다.
> - LOTTO: 1 또는 2
> - PENSION: 1 (MVP 기준)

* **테스트 항목** (예정)

  * bbox 필터 정상 동작 여부
  * SQL 인젝션/에러 방어 처리

---

### 데이터베이스 설계

* **파일 위치** (예정): `db/schema.ts`

* **테이블** (예정)

  * `draws`: 회차 정보
  * `stores`: 판매점 정보 (주소, 좌표, 정규화 필드)
  * `winning_records`: 회차별 당첨 내역
  * `geocode_cache`: 주소 → 좌표 캐시
  * `job_runs`: 크롤링/지오코딩 작업 로그

* **현재 데이터 구조**: `types.ts`의 TypeScript 인터페이스로 정의됨

---

### 크롤링 및 지오코딩 파이프라인

* **ETL Crawler** (예정)

  * 동행복권 JSON → 최신 회차 확인
  * 동행복권 HTML → 판매점 정보 파싱
  * 정규화 후 Pub/Sub 메시지 발행

* **Geocode Worker** (예정)

  * Pub/Sub 메시지 수신 → 주소 캐시 조회
  * Kakao Local API 호출 → 좌표 DB 반영

* **테스트 항목** (예정)

  * HTML 파싱 실패 시 오류 로그 남김
  * 중복 판매점(alias) 처리 정상 동작
  * 지오코딩 실패 시 재시도 수행

---

## 4. 페이지 & 파일 구조 (현재)

```
luckymap-korea/
 ├── App.tsx                    # 메인 앱 컴포넌트
 ├── index.tsx                  # React DOM 진입점
 ├── index.html                 # HTML 템플릿
 ├── vite.config.ts             # Vite 설정
 ├── tsconfig.json              # TypeScript 설정
 ├── package.json               # 의존성 관리
 ├── types.ts                   # TypeScript 타입 정의
 ├── constants.ts               # 상수 및 목업 데이터 (MOCK_STORES)
 ├── components/
 │    ├── MapContainer.tsx      # Kakao Map 지도 컴포넌트
 │    ├── Sidebar.tsx           # 사이드바 (탭, 필터, 리스트)
 │    └── StoreCard.tsx         # 판매점 카드 컴포넌트
 └── Docs/
      ├── PRD.md                # 제품 요구사항 문서
      ├── TechReader.md         # 기능명세서 (이 문서)
      ├── DB.md                 # 데이터베이스 설계서
      └── Design.md             # UI/UX 디자인 가이드
```

---

## 5. QA / 테스트 체크리스트

* **프론트엔드** ✅

  * ✅ 복권 종류 필터 → 결과 정확히 필터링
  * ✅ 지도 줌 인/아웃 → 마커 표시 정상 동작
  * ✅ 마커 클릭 → 인포윈도우 표시
  * ✅ 카드 클릭 → 지도 이동 및 선택 표시
  * ✅ 랭킹 탭 → 지역 필터 동작
  * ✅ 모바일 반응형 동작 (사이드바 드로어)

* **백엔드** (향후 구현)

  * 크롤링 실패 시 로그 남김
  * 지오코딩 캐시 동작 확인
  * API 응답 속도 < 500ms 유지

* **운영** (향후 구현)

  * 토요일 21:10 KST 데이터 업데이트 성공 여부
  * DB 집계 뷰(store_stats) 정상 반영 여부

---
