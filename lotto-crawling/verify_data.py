#!/usr/bin/env python3
"""
Supabase 데이터 전체 검증 스크립트
"""
import os
import sys
from pathlib import Path

def get_database_url():
    """환경변수 또는 .env.local에서 DATABASE_URL을 읽어옵니다."""
    database_url = os.getenv('DATABASE_URL') or os.getenv('SUPABASE_DB_URL')
    if database_url:
        return database_url

    env_file = Path(__file__).parent.parent / '.env.local'
    if env_file.exists():
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key in ('DATABASE_URL', 'SUPABASE_DB_URL'):
                            return value
        except PermissionError:
            pass

    return None


def main():
    print("=" * 70)
    print("Supabase 데이터 전체 검증")
    print("=" * 70)

    database_url = get_database_url()
    if not database_url:
        print("❌ DATABASE_URL 환경변수를 찾을 수 없습니다.")
        sys.exit(1)

    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2가 설치되지 않았습니다.")
        sys.exit(1)

    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()

    try:
        # ============================================
        # 1. draws 테이블
        # ============================================
        print("\n" + "=" * 70)
        print("1. draws 테이블")
        print("=" * 70)

        cursor.execute("""
            SELECT lottery_type, COUNT(*), MIN(round_no), MAX(round_no), MIN(draw_date), MAX(draw_date)
            FROM draws
            GROUP BY lottery_type
            ORDER BY lottery_type;
        """)
        print(f"\n{'복권종류':<10} {'회차수':>8} {'회차범위':>15} {'추첨일범위':>25}")
        print("-" * 60)
        for row in cursor.fetchall():
            print(f"{row[0]:<10} {row[1]:>8} {row[2]:>6} ~ {row[3]:<6} {str(row[4]):>12} ~ {str(row[5]):<12}")

        # draw_date NULL 체크
        cursor.execute("SELECT COUNT(*) FROM draws WHERE draw_date IS NULL;")
        null_dates = cursor.fetchone()[0]
        if null_dates > 0:
            print(f"\n⚠️  draw_date가 NULL인 레코드: {null_dates}개")
        else:
            print(f"\n✅ 모든 draw_date가 설정됨")

        # ============================================
        # 2. stores 테이블
        # ============================================
        print("\n" + "=" * 70)
        print("2. stores 테이블")
        print("=" * 70)

        cursor.execute("SELECT COUNT(*) FROM stores;")
        total_stores = cursor.fetchone()[0]
        print(f"\n총 판매점 수: {total_stores:,}개")

        cursor.execute("SELECT COUNT(*) FROM stores WHERE lat IS NOT NULL AND lng IS NOT NULL;")
        with_coords = cursor.fetchone()[0]
        print(f"좌표 있는 판매점: {with_coords:,}개")
        print(f"좌표 없는 판매점: {total_stores - with_coords:,}개")

        # 좌표 없는 판매점 샘플
        if total_stores - with_coords > 0:
            cursor.execute("""
                SELECT source_id, name, address_raw
                FROM stores
                WHERE lat IS NULL OR lng IS NULL
                LIMIT 5;
            """)
            print("\n좌표 없는 판매점 샘플:")
            for row in cursor.fetchall():
                print(f"  - [{row[0]}] {row[1]}: {row[2][:50]}...")

        # ============================================
        # 3. winning_records 테이블
        # ============================================
        print("\n" + "=" * 70)
        print("3. winning_records 테이블")
        print("=" * 70)

        cursor.execute("""
            SELECT lottery_type, rank, COUNT(*)
            FROM winning_records
            GROUP BY lottery_type, rank
            ORDER BY lottery_type, rank;
        """)
        print(f"\n{'복권종류':<10} {'등수':>6} {'건수':>10}")
        print("-" * 30)
        for row in cursor.fetchall():
            rank_str = f"{row[1]}등" if row[1] > 0 else "보너스"
            print(f"{row[0]:<10} {rank_str:>6} {row[2]:>10,}")

        # method 통계
        cursor.execute("""
            SELECT method, COUNT(*)
            FROM winning_records
            GROUP BY method
            ORDER BY COUNT(*) DESC;
        """)
        print(f"\n방법별 통계:")
        for row in cursor.fetchall():
            print(f"  - {row[0]}: {row[1]:,}건")

        # won_at NULL 체크
        cursor.execute("SELECT COUNT(*) FROM winning_records WHERE won_at IS NULL;")
        null_won_at = cursor.fetchone()[0]
        if null_won_at > 0:
            print(f"\n⚠️  won_at이 NULL인 레코드: {null_won_at}개")
        else:
            print(f"\n✅ 모든 won_at이 설정됨")

        # won_at 범위
        cursor.execute("""
            SELECT lottery_type, MIN(won_at), MAX(won_at)
            FROM winning_records
            GROUP BY lottery_type;
        """)
        print(f"\nwon_at 범위:")
        for row in cursor.fetchall():
            print(f"  - {row[0]}: {row[1]} ~ {row[2]}")

        # ============================================
        # 4. store_stats 테이블
        # ============================================
        print("\n" + "=" * 70)
        print("4. store_stats 테이블")
        print("=" * 70)

        cursor.execute("SELECT COUNT(*) FROM store_stats;")
        total_stats = cursor.fetchone()[0]
        print(f"\n총 레코드 수: {total_stats:,}개")

        cursor.execute("""
            SELECT
                SUM(total_lotto_first_prize) AS lotto_1st,
                SUM(total_lotto_second_prize) AS lotto_2nd,
                SUM(total_pension_first_prize) AS pension_1st,
                SUM(recent_lotto_first_prize) AS recent_lotto_1st,
                SUM(recent_lotto_second_prize) AS recent_lotto_2nd,
                SUM(recent_pension_first_prize) AS recent_pension_1st
            FROM store_stats;
        """)
        row = cursor.fetchone()
        print(f"\n전체 통계 합계:")
        print(f"  - 로또 1등: {row[0]:,}건")
        print(f"  - 로또 2등: {row[1]:,}건")
        print(f"  - 연금복권 1등: {row[2]:,}건")
        print(f"\n최근 1년 통계 합계:")
        print(f"  - 로또 1등: {row[3]:,}건")
        print(f"  - 로또 2등: {row[4]:,}건")
        print(f"  - 연금복권 1등: {row[5]:,}건")

        # winning_records와 일치 여부 검증
        cursor.execute("""
            SELECT COUNT(*) FROM winning_records WHERE lottery_type = 'LOTTO' AND rank = 1;
        """)
        wr_lotto_1st = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(total_lotto_first_prize) FROM store_stats;")
        ss_lotto_1st = cursor.fetchone()[0]

        if wr_lotto_1st == ss_lotto_1st:
            print(f"\n✅ winning_records와 store_stats 일치 (로또 1등: {wr_lotto_1st:,}건)")
        else:
            print(f"\n⚠️  불일치! winning_records: {wr_lotto_1st}, store_stats: {ss_lotto_1st}")

        # ============================================
        # 5. store_name_history 테이블
        # ============================================
        print("\n" + "=" * 70)
        print("5. store_name_history 테이블")
        print("=" * 70)

        cursor.execute("SELECT COUNT(*) FROM store_name_history;")
        history_count = cursor.fetchone()[0]
        print(f"\n총 이력 수: {history_count:,}개")
        if history_count == 0:
            print("  (초기 적재 시 이력 없음 - 정상)")

        # ============================================
        # 6. geocode_cache 테이블
        # ============================================
        print("\n" + "=" * 70)
        print("6. geocode_cache 테이블")
        print("=" * 70)

        cursor.execute("SELECT COUNT(*) FROM geocode_cache;")
        cache_count = cursor.fetchone()[0]
        print(f"\n캐시된 주소 수: {cache_count:,}개")

        # ============================================
        # 7. job_runs 테이블
        # ============================================
        print("\n" + "=" * 70)
        print("7. job_runs 테이블")
        print("=" * 70)

        cursor.execute("SELECT COUNT(*) FROM job_runs;")
        job_count = cursor.fetchone()[0]
        print(f"\n작업 실행 로그 수: {job_count:,}개")

        # ============================================
        # 8. 데이터 정합성 검증
        # ============================================
        print("\n" + "=" * 70)
        print("8. 데이터 정합성 검증")
        print("=" * 70)

        # FK 정합성: winning_records -> draws
        cursor.execute("""
            SELECT COUNT(*)
            FROM winning_records wr
            LEFT JOIN draws d ON wr.draw_id = d.round_no AND wr.lottery_type = d.lottery_type
            WHERE d.round_no IS NULL;
        """)
        orphan_records = cursor.fetchone()[0]
        if orphan_records == 0:
            print("\n✅ winning_records → draws FK 정합성 OK")
        else:
            print(f"\n⚠️  draws에 없는 winning_records: {orphan_records}개")

        # FK 정합성: winning_records -> stores
        cursor.execute("""
            SELECT COUNT(*)
            FROM winning_records wr
            LEFT JOIN stores s ON wr.store_id = s.id
            WHERE s.id IS NULL;
        """)
        orphan_stores = cursor.fetchone()[0]
        if orphan_stores == 0:
            print("✅ winning_records → stores FK 정합성 OK")
        else:
            print(f"⚠️  stores에 없는 winning_records: {orphan_stores}개")

        # FK 정합성: store_stats -> stores
        cursor.execute("""
            SELECT COUNT(*)
            FROM store_stats ss
            LEFT JOIN stores s ON ss.store_id = s.id
            WHERE s.id IS NULL;
        """)
        orphan_stats = cursor.fetchone()[0]
        if orphan_stats == 0:
            print("✅ store_stats → stores FK 정합성 OK")
        else:
            print(f"⚠️  stores에 없는 store_stats: {orphan_stats}개")

        # store_stats 누락 체크
        cursor.execute("""
            SELECT COUNT(DISTINCT store_id) FROM winning_records;
        """)
        unique_stores_in_wr = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM store_stats;")
        stats_count = cursor.fetchone()[0]

        if unique_stores_in_wr == stats_count:
            print(f"✅ store_stats 완전성 OK ({stats_count:,}개)")
        else:
            print(f"⚠️  store_stats 누락: winning_records에 {unique_stores_in_wr}개, store_stats에 {stats_count}개")

        # ============================================
        # 9. 샘플 데이터
        # ============================================
        print("\n" + "=" * 70)
        print("9. 샘플 데이터 (최근 로또 1등 당첨 5건)")
        print("=" * 70)

        cursor.execute("""
            SELECT wr.draw_id, wr.won_at, wr.method, s.name, s.address_raw
            FROM winning_records wr
            JOIN stores s ON wr.store_id = s.id
            WHERE wr.lottery_type = 'LOTTO' AND wr.rank = 1
            ORDER BY wr.draw_id DESC, wr.won_at DESC
            LIMIT 5;
        """)
        print()
        for row in cursor.fetchall():
            print(f"  {row[0]}회차 ({row[1]}) [{row[2]}]")
            print(f"    {row[3]}")
            print(f"    {row[4]}")
            print()

        print("=" * 70)
        print("✅ 데이터 검증 완료!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    main()
