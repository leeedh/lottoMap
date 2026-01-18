-- ============================================
-- 데이터베이스 스키마 생성 스크립트
-- Docs/DB.md 기반
-- ============================================

-- 1) draws 테이블: 회차 정보
CREATE TABLE IF NOT EXISTS draws (
    round_no INT PRIMARY KEY,
    draw_date DATE NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ NULL
);

-- 2) stores 테이블: 판매점 정보
CREATE TABLE IF NOT EXISTS stores (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    address_raw TEXT NOT NULL,
    address_norm TEXT NOT NULL,
    lat DOUBLE PRECISION NULL,
    lng DOUBLE PRECISION NULL,
    source_id VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ NULL,
    CONSTRAINT stores_source_id_unique UNIQUE (source_id)
);

-- 3) winning_records 테이블: 당첨 기록
CREATE TABLE IF NOT EXISTS winning_records (
    source_row_hash VARCHAR(64) PRIMARY KEY,
    draw_id INT NOT NULL REFERENCES draws(round_no),
    store_id BIGINT NOT NULL REFERENCES stores(id),
    lottery_type VARCHAR(10) NOT NULL CHECK (lottery_type IN ('LOTTO','PENSION')),
    rank SMALLINT NOT NULL,
    method VARCHAR(10) NOT NULL DEFAULT 'UNKNOWN' CHECK (method IN ('AUTO','MANUAL','SEMI','UNKNOWN')),
    source_seq INTEGER NULL,
    won_at DATE NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT winning_records_rank_check CHECK (
        (lottery_type='LOTTO' AND rank IN (1,2)) OR 
        (lottery_type='PENSION' AND rank IN (1))
    )
);

-- winning_records 인덱스
CREATE INDEX IF NOT EXISTS idx_winning_records_draw_lottery_rank 
    ON winning_records(draw_id, lottery_type, rank);
CREATE INDEX IF NOT EXISTS idx_winning_records_store_lottery_rank 
    ON winning_records(store_id, lottery_type, rank);
CREATE INDEX IF NOT EXISTS idx_winning_records_won_at 
    ON winning_records(won_at);
CREATE INDEX IF NOT EXISTS idx_winning_records_method 
    ON winning_records(method);

-- 4) geocode_cache 테이블: 주소 -> 좌표 캐시
CREATE TABLE IF NOT EXISTS geocode_cache (
    id BIGSERIAL PRIMARY KEY,
    address_hash VARCHAR(64) NOT NULL,
    address TEXT NOT NULL,
    lat DOUBLE PRECISION NOT NULL,
    lng DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT geocode_cache_address_hash_unique UNIQUE (address_hash)
);

-- 5) store_stats 테이블: 판매점 통계 (집계용)
CREATE TABLE IF NOT EXISTS store_stats (
    store_id BIGINT PRIMARY KEY REFERENCES stores(id),
    total_lotto_first_prize INT DEFAULT 0,
    total_lotto_second_prize INT DEFAULT 0,
    total_pension_first_prize INT DEFAULT 0,
    recent_lotto_first_prize INT DEFAULT 0,
    recent_lotto_second_prize INT DEFAULT 0,
    recent_pension_first_prize INT DEFAULT 0,
    last_won_at DATE NULL,
    last_updated_at TIMESTAMPTZ NULL
);

-- 6) store_name_history 테이블: 판매점명 변경 이력
CREATE TABLE IF NOT EXISTS store_name_history (
    id BIGSERIAL PRIMARY KEY,
    store_id BIGINT NOT NULL REFERENCES stores(id),
    old_name TEXT NOT NULL,
    new_name TEXT NOT NULL,
    old_name_normalized TEXT NOT NULL,
    new_name_normalized TEXT NOT NULL,
    drw_no INT NOT NULL REFERENCES draws(round_no),
    is_significant_change BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_store_name_history_store_drw 
    ON store_name_history(store_id, drw_no DESC);

-- 7) job_runs 테이블: 작업 실행 로그
CREATE TABLE IF NOT EXISTS job_runs (
    id BIGSERIAL PRIMARY KEY,
    job_name VARCHAR(100) NOT NULL,
    run_at TIMESTAMPTZ DEFAULT now(),
    status VARCHAR(20) NOT NULL CHECK (status IN ('STARTED','COMPLETED','FAILED')),
    target_round_no INT NULL,
    records_processed INT DEFAULT 0,
    error_message TEXT NULL,
    duration_ms BIGINT NULL
);
