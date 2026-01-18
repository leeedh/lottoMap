# 데이터베이스 설계서(최신)

## 현재 상태

**데이터베이스**: 현재 미구현 - 목업 데이터 사용 중  
**데이터 구조**: TypeScript 인터페이스로 정의됨 (`types.ts`)

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

## 향후 데이터베이스 설계 (PostgreSQL - Supabase 예정)

### 1) `draws`

- 컬럼
  - `round_no` INT PRIMARY KEY ← CSV `회차`
  - `draw_date` DATE NULL (룰 또는 외부 소스로 채움)
  - `created_at` TIMESTAMPTZ DEFAULT now()
  - `updated_at` TIMESTAMPTZ NULL (자동 갱신 제거)
- 비고: 현재 `draw_date`는 주 1회(토) 규칙으로 보정 가능

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
  - `updated_at` TIMESTAMPTZ NULL (자동 갱신 제거)
- 제약/인덱스
  - UNIQUE (`source_id`)
  - 필요 시 텍스트/지오 인덱스 추가 고려

### 3) `winning_records`

- 컬럼
  - `source_row_hash` VARCHAR(64) PRIMARY KEY (idempotent upsert 키)
  - `draw_id` INT NOT NULL REFERENCES `draws`(`round_no`)
  - `store_id` BIGINT NOT NULL REFERENCES `stores`(`id`)
  - `lottery_type` VARCHAR(10) NOT NULL CHECK (lottery_type IN ('LOTTO','PENSION'))  -- 복권 종류 (현재는 LOTTO만 적재)
  - `rank` SMALLINT NOT NULL
  - `method` VARCHAR(10) NOT NULL DEFAULT 'UNKNOWN' CHECK (method IN ('AUTO','MANUAL','SEMI','UNKNOWN'))
  - `source_seq` INTEGER NULL  -- CSV `번호` (동일 회차/판매점/등수 내 다중 당첨 구분용)
  - `won_at` DATE NULL
  - `created_at` TIMESTAMPTZ DEFAULT now()
- 인덱스
  - (`draw_id`, `lottery_type`, `rank`), (`store_id`, `lottery_type`, `rank`), (`won_at`), (`method`)
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
  - 필요 시 `UNIQUE(address_hash)` 또는 `UNIQUE(address_hash, lat, lng)` 채택

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
  - `drw_no` INT NOT NULL REFERENCES `draws`(`round_no`)
  - `is_significant_change` BOOLEAN NOT NULL DEFAULT false
  - `created_at` TIMESTAMPTZ DEFAULT now()
- 인덱스
  - (`store_id`, `drw_no` DESC)

---

---

## 원천 → 스테이징/정규화 매핑 (향후 구현 예정)
> 참고
> - 현재 수집된 데이터는 `lotto-crawling/lotto_all_rounds.csv`(로또6/45 당첨 판매점)입니다.
> - 향후에는 동행복권 JSON API 호출이 가능하면 API를 1순위로 사용하고, 불가 시 현재처럼 Playwright 기반 HTML 추출을 백업 경로로 둡니다.
> - 원천 포맷(CSV/JSON/HTML)과 무관하게, 아래 스테이징 형태로 정규화한 후 본 테이블로 적재합니다.

## `stg_winning_store_rows` (임시 스테이징)

- `lottery_type` TEXT NOT NULL                 -- 'LOTTO' | 'PENSION' (원천 파일/크롤러 설정으로 주입)
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
- `crawled_at` TIMESTAMPTZ NULL               ← CSV `크롤링시간`
- `loaded_at` TIMESTAMPTZ DEFAULT now()
- `source_row_hash` VARCHAR(64) UNIQUE        -- 멱등 적재 키

## 변환 규칙

1. 회차 upsert: `draws.round_no = round_no` (없으면 insert)
2. 판매점 upsert: `stores`를 `source_id = store_source_id`로 upsert (UNIQUE)
   - `name`, `address_raw` 저장 → `address_norm` 정규화
   - 좌표가 유효하면(`lat/lng` 범위 검증 통과) `stores.lat/lng` 업데이트
   - 좌표가 없거나 이상치면 → `geocode_cache` 조회 → 미스 시 카카오 지오코딩(주소→키워드 순) → 캐시 저장
3. 방법 정규화: `method_raw` -> `method` 매핑(AUTO/MANUAL/SEMI/UNKNOWN). 빈값은 UNKNOWN
4. 당첨내역 upsert: `winning_records`
   - `draw_id`(조인), `store_id`(조인), `lottery_type`, `rank`, `method`, `source_seq`
   - `source_row_hash = sha256(round_no|lottery_type|store_source_id|rank|source_seq)`로 idempotent upsert
5. 집계 갱신: 배치 적재 후 `store_stats`를 재계산하거나, 적재 시점에 증분 upsert(ON CONFLICT (store_id))
6. 이름 변경 이력: 기존 이름과 신규 이름 비교 후 `store_name_history` 기록(의미있는 변경만 구분)

---

---

## API/검색 영향 (향후 구현 시 검증 포인트)

- `/api/stores?bbox=&q=&rank=`: 집계(`store_stats`)를 활용한 1·2등 보유 여부 응답. 자동/수동 필터는 `winning_records.method`
- `/api/stores/:id/history`: 이름 변경 이력 제공(정규화/의미있는 변경 여부 포함)
- `/api/rankings`: 동일. 필요 시 method 필터 추가 가능

---

---

## 인덱스/제약 최종 점검 (향후 구현 시)

* **UNIQUE**: 
  * `stores(source_id)`
  * `winning_records(source_row_hash)`
  * `draws(round_no)`

* **CHECK**: 
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

## TypeScript 인터페이스 → 데이터베이스 매핑 (향후 구현 시)

현재 TypeScript 인터페이스 구조와 향후 데이터베이스 구조의 매핑 관계:

* `Store` → `stores` 테이블
  * `wins` (WinStats) → `store_stats` 테이블에서 집계
  * `history` (WinRecord[]) → `winning_records` 테이블 조회
  * `primaryCategory` → `winning_records`에서 가장 많은 당첨 종류 기반

* `WinRecord` → `winning_records` 테이블
  * `method` → `method` 컬럼 (AUTO/MANUAL/SEMI/UNKNOWN)
  * `type` → `rank` 및 `lottery_type` 컬럼으로 구분

* `WinStats` → `store_stats` 테이블에서 집계
  * `lotto1` → `total_lotto_first_prize` (lottery_type=LOTTO, rank=1)
  * `lotto2` → `total_lotto_second_prize` (lottery_type=LOTTO, rank=2)
  * `pension` → `total_pension_first_prize` (lottery_type=PENSION, rank=1)

---

## 자동화 작업 로그 (운영 필수)

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