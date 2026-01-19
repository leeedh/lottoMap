# 데이터베이스 설계서(최신)

## 현재 상태

**데이터베이스**: Supabase PostgreSQL (구현 완료)
**데이터 구조**: TypeScript 인터페이스로 정의됨 (`types.ts`)

### 현재 데이터 현황

| 테이블 | 레코드 수 | 비고 |
|--------|----------|------|
| `draws` | 1,504개 | 로또 1,206개 + 연금복권 298개 |
| `stores` | 10,589개 | 좌표 있음: 10,588 / 없음: 1 |
| `winning_records` | 65,333개 | 로또 61,787 + 연금복권 3,546 |

### 추첨일 규칙

| 복권 종류 | 1회차 시작일 | 추첨 요일 | 계산식 |
|----------|-------------|----------|--------|
| 로또 6/45 | 2002-12-07 (토) | 매주 토요일 | `2002-12-07 + (회차-1) * 7일` |
| 연금복권 720+ | 2020-05-07 (목) | 매주 목요일 | `2020-05-07 + (회차-1) * 7일` |

### 현재 데이터 구조 (TypeScript)

현재는 `types.ts`에서 다음과 같은 TypeScript 인터페이스로 데이터 구조를 정의하고 있습니다:

* `Store`: 판매점 정보
  * `id`: string
  * `name`: string
  * `address`: string
  * `lat`: number
  * `lng`: number
  * `wins`: WinStats (당첨 통계)
  * `history`: WinRecord[] (당첨 이력)
  * `primaryCategory`: LotteryType (주 카테고리)

* `WinRecord`: 당첨 기록
  * `id`: string
  * `type`: LotteryType (LOTTO | PENSION)
  * `round`: number (회차)
  * `rank`: number (등수: 1 or 2 for Lotto, 1 for Pension)
  * `method?`: LottoMethod (로또인 경우만: 자동, 수동, 반자동)
  * `date`: string

* `WinStats`: 당첨 통계
  * `lotto1`: number (로또 1등 횟수)
  * `lotto2`: number (로또 2등 횟수)
  * `pension`: number (연금복권 1등 횟수)

* `LotteryType`: 복권 종류 (LOTTO | PENSION)

---

## 데이터베이스 설계 (PostgreSQL - Supabase)

### 1) `draws`

- 컬럼
  - `round_no` INT NOT NULL ← CSV `회차`
  - `lottery_type` VARCHAR(10) NOT NULL CHECK (lottery_type IN ('LOTTO','PENSION')) ← 복권 종류
  - `draw_date` DATE NULL (추첨일: 로또는 토요일, 연금복권은 목요일)
  - `created_at` TIMESTAMPTZ DEFAULT now()
  - `updated_at` TIMESTAMPTZ NULL
- 제약/인덱스
  - **PRIMARY KEY (`round_no`, `lottery_type`)** ← 복합 PK
- 비고
  - 로또 6/45: 2002-12-07 1회차, 매주 토요일
  - 연금복권 720+: 2020-05-07 1회차, 매주 목요일

### 2) `stores`

- 컬럼
  - `id` BIGSERIAL PRIMARY KEY
  - `name` VARCHAR(200) NOT NULL
  - `address_raw` TEXT NOT NULL
  - `address_norm` TEXT NOT NULL
  - `lat` DOUBLE PRECISION NULL
  - `lng` DOUBLE PRECISION NULL
  - `source_id` VARCHAR(100) NOT NULL ← CSV `판매점ID` (동행복권 판매점 고유 ID)
  - `is_active` BOOLEAN DEFAULT TRUE
  - `created_at` TIMESTAMPTZ DEFAULT now()
  - `updated_at` TIMESTAMPTZ NULL
- 제약/인덱스
  - UNIQUE (`source_id`)
  - 필요 시 텍스트/지오 인덱스 추가 고려

### 3) `winning_records`

- 컬럼
  - `source_row_hash` VARCHAR(64) PRIMARY KEY (idempotent upsert 키)
  - `draw_id` INT NOT NULL ← 회차 번호
  - `store_id` BIGINT NOT NULL REFERENCES `stores`(`id`)
  - `lottery_type` VARCHAR(10) NOT NULL CHECK (lottery_type IN ('LOTTO','PENSION'))  -- 복권 종류
  - `rank` SMALLINT NOT NULL
  - `method` VARCHAR(10) NOT NULL DEFAULT 'UNKNOWN' CHECK (method IN ('AUTO','MANUAL','SEMI','UNKNOWN'))
  - `source_seq` INTEGER NULL  -- CSV `번호` (동일 회차/판매점/등수 내 다중 당첨 구분용)
  - `won_at` DATE NULL ← 당첨일 (draws.draw_date와 동일)
  - `created_at` TIMESTAMPTZ DEFAULT now()
- 제약/인덱스
  - **FOREIGN KEY (`draw_id`, `lottery_type`) REFERENCES `draws`(`round_no`, `lottery_type`)** ← 복합 FK
  - INDEX (`draw_id`, `lottery_type`, `rank`)
  - INDEX (`store_id`, `lottery_type`, `rank`)
  - INDEX (`won_at`)
  - INDEX (`method`)
- 매핑
  - `'자동'→AUTO`, `'수동'→MANUAL`, `'반자동'→SEMI`, 빈값/그 외→UNKNOWN
- 타입별 제약(권장)
  - 목적: 로또/연금복권을 같은 테이블로 수집/적재하면서도 제약 위반으로 ETL이 멈추는 것을 방지
  - CHECK 예시:
    - `((lottery_type='LOTTO' AND rank IN (1,2)) OR (lottery_type='PENSION' AND rank IN (0,1,2)))`
    - (권장) `method`는 현재 원천(CSV/HTML)에서 빈 값이 존재하므로 `UNKNOWN`으로 흡수하여 NOT NULL 유지
- 고유해시 예시
  - (권장) **내부 PK(store_id)가 아닌 원천 키 기반으로 생성**
  - `sha256(concat(round_no,'|',lottery_type,'|',store_source_id,'|',rank,'|',coalesce(source_seq,0)))`

### 4) `geocode_cache`

- 컬럼
  - `id` BIGSERIAL PRIMARY KEY
  - `address_hash` VARCHAR(64) NOT NULL
  - `address` TEXT NOT NULL
  - `lat` DOUBLE PRECISION NOT NULL
  - `lng` DOUBLE PRECISION NOT NULL
  - `created_at` TIMESTAMPTZ DEFAULT now()
- 제약
  - UNIQUE(`address_hash`)

### 5) `store_stats`

- 목적: 랭킹/목록 응답 가속을 위한 누적 통계
- 컬럼
  - `store_id` BIGINT PRIMARY KEY REFERENCES `stores`(`id`)
  - `total_lotto_first_prize` INT DEFAULT 0
  - `total_lotto_second_prize` INT DEFAULT 0
  - `total_pension_first_prize` INT DEFAULT 0
  - `recent_lotto_first_prize` INT DEFAULT 0
  - `recent_lotto_second_prize` INT DEFAULT 0
  - `recent_pension_first_prize` INT DEFAULT 0
  - `last_won_at` DATE NULL
  - `last_updated_at` TIMESTAMPTZ NULL
- 비고: 별도 `id` 컬럼 제거, 업서트는 `ON CONFLICT (store_id)` 기준

### 6) `store_name_history`

- 목적: 판매점명 변경 이력 추적(형식 차이와 의미있는 변경 구분)
- 컬럼
  - `id` BIGSERIAL PRIMARY KEY
  - `store_id` BIGINT NOT NULL REFERENCES `stores`(`id`)
  - `old_name` TEXT NOT NULL
  - `new_name` TEXT NOT NULL
  - `old_name_normalized` TEXT NOT NULL
  - `new_name_normalized` TEXT NOT NULL
  - `drw_no` INT NOT NULL
  - `lottery_type` VARCHAR(10) NOT NULL DEFAULT 'LOTTO'
  - `is_significant_change` BOOLEAN NOT NULL DEFAULT false
  - `created_at` TIMESTAMPTZ DEFAULT now()
- 인덱스
  - (`store_id`, `drw_no` DESC)
- 비고: FK 제약조건 제거됨 (복합 PK 변경으로 인해)

### 7) `job_runs`

- 목적: 크롤러/지오코딩/집계 작업의 실행 이력, 성공/실패, 처리량, 오류를 기록
- 컬럼(예시)
  - `id` BIGSERIAL PRIMARY KEY
  - `job_name` VARCHAR(100) NOT NULL  -- 'etl-crawler', 'geocode-worker' 등
  - `run_at` TIMESTAMPTZ DEFAULT now()
  - `status` VARCHAR(20) NOT NULL CHECK (status IN ('STARTED','COMPLETED','FAILED'))
  - `target_round_no` INT NULL
  - `records_processed` INT DEFAULT 0
  - `error_message` TEXT NULL
  - `duration_ms` BIGINT NULL

---

## 원천 → 스테이징/정규화 매핑

> 참고
> - 현재 수집된 데이터는 `lotto-crawling/all_lottery_stores.csv` (로또 + 연금복권 통합)입니다.
> - CSV 파일에는 `복권종류` 컬럼이 포함되어 있으며, 'lotto' 또는 'pension' 값을 가집니다.
> - 향후에는 동행복권 JSON API 호출이 가능하면 API를 1순위로 사용하고, 불가 시 현재처럼 Playwright 기반 HTML 추출을 백업 경로로 둡니다.
> - 원천 포맷(CSV/JSON/HTML)과 무관하게, 아래 스테이징 형태로 정규화한 후 본 테이블로 적재합니다.

## `stg_winning_store_rows` (임시 스테이징)

- `lottery_type` TEXT NOT NULL                 -- 'LOTTO' | 'PENSION' (CSV `복권종류` 컬럼에서 매핑: 'lotto'→'LOTTO', 'pension'→'PENSION')
- `round_no` INT NOT NULL                     ← CSV `회차`
- `store_source_id` TEXT NOT NULL             ← CSV `판매점ID`
- `source_seq` INT NULL                       ← CSV `번호`
- `store_name` TEXT NOT NULL                  ← CSV `판매점명`
- `prize_raw` TEXT NOT NULL                   ← CSV `등수` (예: '1등','2등','보너스')
- `rank` SMALLINT NOT NULL                    -- `prize_raw` 정규화 결과 (권장: 1등→1, 2등→2, 보너스→0)
- `method_raw` TEXT NULL                      ← CSV `자동수동`(자동/수동/반자동/빈값)
- `address_raw` TEXT NOT NULL                 ← CSV `주소`
- `region_raw` TEXT NULL                      ← CSV `지역`(빈값 가능)
- `phone_raw` TEXT NULL                       ← CSV `전화번호`
- `products_raw` TEXT NULL                    ← CSV `취급복권`
- `lat` DOUBLE PRECISION NULL                 ← CSV `위도`
- `lng` DOUBLE PRECISION NULL                 ← CSV `경도`
- `loaded_at` TIMESTAMPTZ DEFAULT now()
- `source_row_hash` VARCHAR(64) UNIQUE        -- 멱등 적재 키

## 변환 규칙

1. 회차 upsert: `draws` 테이블에 `(round_no, lottery_type)` 복합키로 upsert
   - `draw_date`는 복권 종류별 규칙으로 계산:
     - 로또: `2002-12-07 + (회차-1) * 7일`
     - 연금복권: `2020-05-07 + (회차-1) * 7일`
2. 판매점 upsert: `stores`를 `source_id = store_source_id`로 upsert (UNIQUE)
   - `name`, `address_raw` 저장 → `address_norm` 정규화
   - 좌표가 유효하면(`lat/lng` 범위 검증 통과) `stores.lat/lng` 업데이트
   - 좌표가 없거나 이상치면 → `geocode_cache` 조회 → 미스 시 카카오 지오코딩(주소→키워드 순) → 캐시 저장
3. 복권 종류 정규화: CSV `복권종류` 컬럼 값('lotto', 'pension')을 대문자로 변환하여 `lottery_type`에 매핑('lotto'→'LOTTO', 'pension'→'PENSION')
4. 방법 정규화: `method_raw` -> `method` 매핑(AUTO/MANUAL/SEMI/UNKNOWN). 빈값은 UNKNOWN
5. 당첨내역 upsert: `winning_records`
   - `draw_id`(회차), `store_id`(조인), `lottery_type`, `rank`, `method`, `source_seq`
   - `won_at`은 해당 회차의 `draw_date`와 동일
   - `source_row_hash = sha256(round_no|lottery_type|store_source_id|rank|source_seq)`로 idempotent upsert
6. 집계 갱신: 배치 적재 후 `store_stats`를 재계산하거나, 적재 시점에 증분 upsert(ON CONFLICT (store_id))
7. 이름 변경 이력: 기존 이름과 신규 이름 비교 후 `store_name_history` 기록(의미있는 변경만 구분)

---

## API/검색 영향 (향후 구현 시 검증 포인트)

- `/api/stores?bbox=&q=&rank=`: 집계(`store_stats`)를 활용한 1·2등 보유 여부 응답. 자동/수동 필터는 `winning_records.method`
- `/api/stores/:id/history`: 이름 변경 이력 제공(정규화/의미있는 변경 여부 포함)
- `/api/rankings`: 동일. 필요 시 method 필터 추가 가능

---

## 인덱스/제약 최종 점검

* **PRIMARY KEY**:
  * `draws(round_no, lottery_type)` ← 복합 PK
  * `stores(id)`
  * `winning_records(source_row_hash)`

* **UNIQUE**:
  * `stores(source_id)`
  * `geocode_cache(address_hash)`

* **FOREIGN KEY**:
  * `winning_records(draw_id, lottery_type)` → `draws(round_no, lottery_type)` ← 복합 FK
  * `winning_records(store_id)` → `stores(id)`
  * `store_stats(store_id)` → `stores(id)`

* **CHECK**:
  * `draws.lottery_type ∈ {LOTTO, PENSION}`
  * `winning_records.lottery_type ∈ {LOTTO, PENSION}`
  * `winning_records.rank`: `lottery_type`별로 허용 등수 범위 정의
  * `winning_records.method ∈ {AUTO,MANUAL,SEMI,UNKNOWN}`

* **인덱스**:
  * 텍스트 검색: `pg_trgm(stores.name, stores.address_norm)`
  * 지리: GIST(geometry) 또는 `(lat,lng)` BTREE
  * 이력/필터:
    * `(winning_records.store_id, rank)`
    * `(won_at DESC)`
    * `(method)`

---

## TypeScript 인터페이스 → 데이터베이스 매핑

현재 TypeScript 인터페이스 구조와 데이터베이스 구조의 매핑 관계:

* `Store` → `stores` 테이블
  * `wins` (WinStats) → `store_stats` 테이블에서 집계
  * `history` (WinRecord[]) → `winning_records` 테이블 조회
  * `primaryCategory` → `winning_records`에서 가장 많은 당첨 종류 기반

* `WinRecord` → `winning_records` 테이블
  * `method` → `method` 컬럼 (AUTO/MANUAL/SEMI/UNKNOWN)
  * `type` → `lottery_type` 컬럼으로 구분
  * `date` → `won_at` 컬럼

* `WinStats` → `store_stats` 테이블에서 집계
  * `lotto1` → `total_lotto_first_prize` (lottery_type=LOTTO, rank=1)
  * `lotto2` → `total_lotto_second_prize` (lottery_type=LOTTO, rank=2)
  * `pension` → `total_pension_first_prize` (lottery_type=PENSION, rank=1)

---

## 데이터 적재 스크립트

| 스크립트 | 설명 |
|---------|------|
| `lotto-crawling/load_data_to_supabase.py` | CSV → Supabase 초기 적재 |
| `lotto-crawling/update_draw_dates.py` | draws 테이블 draw_date 업데이트 (로또) |
| `lotto-crawling/update_won_at.py` | winning_records 테이블 won_at 업데이트 |
| `lotto-crawling/migrate_draws_schema.py` | draws 테이블 스키마 마이그레이션 (lottery_type 추가) |
| `lotto-crawling/fix_pension_dates.py` | 연금복권 추첨일 수정 |
| `lotto-crawling/populate_store_stats.py` | store_stats 테이블 집계 데이터 생성 |
| `lotto-crawling/verify_data.py` | 데이터 검증 |

### store_stats 집계 현황

| 항목 | 전체 | 최근 1년 |
|-----|------|---------|
| 로또 1등 | 8,743건 | 817건 |
| 로또 2등 | 53,044건 | 4,824건 |
| 연금복권 1등 | 348건 | 67건 |

### store_name_history 테이블

- 초기 적재 시에는 이력이 없음 (정상)
- 향후 데이터 업데이트 시 판매점명 변경이 감지되면 자동으로 기록됨

---
