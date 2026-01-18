-- ============================================
-- 테스트 INSERT 쿼리
-- 테이블 생성 후 실행하여 정상 동작 확인
-- ============================================

-- 1. draws 테이블 테스트 데이터 삽입
INSERT INTO draws (round_no, draw_date) 
VALUES (1150, '2025-01-18')
ON CONFLICT (round_no) DO NOTHING;

-- 2. stores 테이블 테스트 데이터 삽입
INSERT INTO stores (name, address_raw, address_norm, lat, lng, source_id)
VALUES 
    ('테스트 판매점 1', '서울특별시 강남구 테헤란로 123', '서울특별시 강남구 테헤란로 123', 37.5665, 126.9780, 'TEST_STORE_001'),
    ('테스트 판매점 2', '서울특별시 서초구 서초대로 456', '서울특별시 서초구 서초대로 456', 37.4837, 127.0324, 'TEST_STORE_002')
ON CONFLICT (source_id) DO NOTHING
RETURNING id, name, source_id;

-- 3. winning_records 테이블 테스트 데이터 삽입
-- 주의: source_row_hash는 SHA-256 해시값이어야 함
-- 여기서는 간단한 테스트를 위해 수동으로 생성
-- 실제 구현에서는: sha256(concat(round_no,'|',lottery_type,'|',store_source_id,'|',rank,'|',coalesce(source_seq,0)))
INSERT INTO winning_records (
    source_row_hash,
    draw_id,
    store_id,
    lottery_type,
    rank,
    method,
    source_seq,
    won_at
)
SELECT 
    -- 해시는 실제로는 애플리케이션에서 생성해야 함
    'test_hash_' || d.round_no || '_' || s.source_id || '_' || 1 as source_row_hash,
    d.round_no,
    s.id,
    'LOTTO',
    1,
    'AUTO',
    1,
    d.draw_date
FROM draws d
CROSS JOIN stores s
WHERE d.round_no = 1150 
  AND s.source_id = 'TEST_STORE_001'
ON CONFLICT (source_row_hash) DO NOTHING;

-- 4. store_stats 테이블 테스트 데이터 삽입/업데이트
INSERT INTO store_stats (
    store_id,
    total_lotto_first_prize,
    total_lotto_second_prize,
    last_won_at
)
SELECT 
    id,
    1,
    0,
    '2025-01-18'
FROM stores
WHERE source_id = 'TEST_STORE_001'
ON CONFLICT (store_id) 
DO UPDATE SET
    total_lotto_first_prize = store_stats.total_lotto_first_prize + EXCLUDED.total_lotto_first_prize,
    last_won_at = EXCLUDED.last_won_at,
    last_updated_at = now();

-- 5. 조회 테스트: 모든 테이블 데이터 확인
SELECT 'draws' as table_name, COUNT(*) as count FROM draws
UNION ALL
SELECT 'stores', COUNT(*) FROM stores
UNION ALL
SELECT 'winning_records', COUNT(*) FROM winning_records
UNION ALL
SELECT 'store_stats', COUNT(*) FROM store_stats;

-- 6. 상세 조회: stores와 winning_records 조인
SELECT 
    s.id,
    s.name,
    s.source_id,
    s.address_norm,
    wr.rank,
    wr.method,
    wr.won_at,
    d.round_no
FROM stores s
LEFT JOIN winning_records wr ON s.id = wr.store_id
LEFT JOIN draws d ON wr.draw_id = d.round_no
WHERE s.source_id LIKE 'TEST_%';
