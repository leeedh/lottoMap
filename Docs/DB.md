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
  - `round_no` INT PRIMARY KEY ← CSV `drw_no`
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
  - `source_id` VARCHAR(100) NOT NULL ← CSV `store_id`
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
  - `lottery_type` VARCHAR(10) NOT NULL CHECK (lottery_type IN ('LOTTO','PENSION'))  -- 복권 종류
  - `rank` SMALLINT NOT NULL CHECK (rank IN (1,2))
  - `method` VARCHAR(10) NULL CHECK (method IN ('AUTO','MANUAL','SEMI','UNKNOWN'))
  - `source_seq` INTEGER NULL
  - `won_at` DATE NULL
  - `created_at` TIMESTAMPTZ DEFAULT now()
- 인덱스
  - (`draw_id`, `lottery_type`, `rank`), (`store_id`, `lottery_type`, `rank`), (`won_at`), (`method`)
- 매핑
  - `'자동'→AUTO`, `'수동'→MANUAL`, `'반자동'→SEMI`, 그 외→UNKNOWN
- 타입별 제약(권장)
  - 목적: 로또/연금복권을 같은 테이블로 수집/적재하면서도 제약 위반으로 ETL이 멈추는 것을 방지
  - CHECK 예시:
    - `((lottery_type='LOTTO' AND rank IN (1,2)) OR (lottery_type='PENSION' AND rank IN (1)))`
    - `((lottery_type='LOTTO' AND method IS NOT NULL) OR (lottery_type='PENSION' AND method IS NULL))`
- 고유해시 예시
  - `sha1(concat(drw_no,'|',lottery_type,'|',store_id,'|',rank,'|',coalesce(category,''),'|',coalesce(number,'')))`

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

## CSV → 스테이징/정규화 매핑 (향후 구현 예정)
> 참고: 현재는 문서상 예시로 CSV 스테이징을 사용했지만, 실제 소스는 "동행복권 공개 엔드포인트(JSON/HTML)"가 될 가능성이 큽니다.
> 따라서 아래 스테이징 섹션은 "원천 포맷(CSV/JSON/HTML)과 무관하게, ETL 적재 전에 거치는 임시 적재 형태"로 이해하면 됩니다.

## `stg_lotto_salespoints` (임시 스테이징)

- `drw_no` INT NOT NULL
- `rank` SMALLINT NOT NULL
- `number` INT NULL  → `source_seq`
- `name` TEXT NOT NULL
- `category` TEXT NULL → `method_raw`
- `address` TEXT NOT NULL
- `store_id` TEXT NOT NULL
- `loaded_at` TIMESTAMPTZ DEFAULT now()
- `source_row_hash` VARCHAR(64) UNIQUE

## 변환 규칙

1. 회차 upsert: `draws.round_no = drw_no` (없으면 insert)
2. 판매점 upsert: `stores`를 `source_id`로 upsert (UNIQUE)
   - `name`, `address_raw` 저장 → `address_norm` 정규화
   - 좌표 없음 → `geocode_cache` 조회 → 미스 시 카카오 지오코딩(주소→키워드 순) → 실패 시 스크래핑 보조(선택) → 캐시 저장
3. 카테고리 정규화: `category` -> `method` 매핑(AUTO/MANUAL/SEMI/UNKNOWN)
4. 당첨내역 upsert: `winning_records`
   - `draw_id`(조인), `store_id`(조인), `rank`, `method`, `source_seq`
   - `source_row_hash`로 idempotent upsert
5. 집계 갱신: 로딩 중 즉시 `store_stats` 누적 (ON CONFLICT (store_id))
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
  * `winning_records.rank ∈ {1,2}`
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