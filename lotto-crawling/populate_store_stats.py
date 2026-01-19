#!/usr/bin/env python3
"""
store_stats 테이블에 집계 데이터를 생성하는 스크립트
winning_records에서 판매점별 당첨 통계를 집계합니다.
"""
import os
import sys
from pathlib import Path
from datetime import date, timedelta

# 최근 기간 정의 (1년)
RECENT_PERIOD_DAYS = 365


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
    print("=" * 60)
    print("store_stats 테이블 집계 데이터 생성")
    print("=" * 60)

    database_url = get_database_url()
    if not database_url:
        print("❌ DATABASE_URL 환경변수를 찾을 수 없습니다.")
        sys.exit(1)

    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    except ImportError:
        print("❌ psycopg2가 설치되지 않았습니다.")
        sys.exit(1)

    print(f"\n🔗 데이터베이스 연결 중...")
    conn = psycopg2.connect(database_url)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    try:
        # 최근 기준일 계산
        recent_cutoff = date.today() - timedelta(days=RECENT_PERIOD_DAYS)
        print(f"  - 최근 기준일: {recent_cutoff} (최근 {RECENT_PERIOD_DAYS}일)")

        # Step 1: 기존 데이터 삭제
        print("\n" + "-" * 40)
        print("Step 1: 기존 store_stats 데이터 삭제")
        cursor.execute("DELETE FROM store_stats;")
        print("  ✅ 삭제 완료")

        # Step 2: 집계 데이터 생성 및 삽입
        print("\n" + "-" * 40)
        print("Step 2: 집계 데이터 생성 및 삽입")

        # 집계 쿼리
        aggregate_sql = """
            INSERT INTO store_stats (
                store_id,
                total_lotto_first_prize,
                total_lotto_second_prize,
                total_pension_first_prize,
                recent_lotto_first_prize,
                recent_lotto_second_prize,
                recent_pension_first_prize,
                last_won_at,
                last_updated_at
            )
            SELECT
                store_id,
                -- 전체 통계
                COUNT(*) FILTER (WHERE lottery_type = 'LOTTO' AND rank = 1) AS total_lotto_first_prize,
                COUNT(*) FILTER (WHERE lottery_type = 'LOTTO' AND rank = 2) AS total_lotto_second_prize,
                COUNT(*) FILTER (WHERE lottery_type = 'PENSION' AND rank = 1) AS total_pension_first_prize,
                -- 최근 통계
                COUNT(*) FILTER (WHERE lottery_type = 'LOTTO' AND rank = 1 AND won_at >= %s) AS recent_lotto_first_prize,
                COUNT(*) FILTER (WHERE lottery_type = 'LOTTO' AND rank = 2 AND won_at >= %s) AS recent_lotto_second_prize,
                COUNT(*) FILTER (WHERE lottery_type = 'PENSION' AND rank = 1 AND won_at >= %s) AS recent_pension_first_prize,
                -- 마지막 당첨일
                MAX(won_at) AS last_won_at,
                now() AS last_updated_at
            FROM winning_records
            GROUP BY store_id;
        """

        cursor.execute(aggregate_sql, (recent_cutoff, recent_cutoff, recent_cutoff))
        print(f"  ✅ 집계 데이터 삽입 완료")

        # Step 3: 검증
        print("\n" + "-" * 40)
        print("검증:")

        cursor.execute("SELECT COUNT(*) FROM store_stats;")
        total_count = cursor.fetchone()[0]
        print(f"  - store_stats 총 레코드: {total_count}개")

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
        print(f"\n  전체 통계:")
        print(f"    - 로또 1등: {row[0]}건")
        print(f"    - 로또 2등: {row[1]}건")
        print(f"    - 연금복권 1등: {row[2]}건")
        print(f"\n  최근 {RECENT_PERIOD_DAYS}일 통계:")
        print(f"    - 로또 1등: {row[3]}건")
        print(f"    - 로또 2등: {row[4]}건")
        print(f"    - 연금복권 1등: {row[5]}건")

        # Top 5 판매점
        print("\n  로또 1등 Top 5 판매점:")
        cursor.execute("""
            SELECT ss.store_id, s.name, ss.total_lotto_first_prize, ss.total_lotto_second_prize
            FROM store_stats ss
            JOIN stores s ON ss.store_id = s.id
            ORDER BY ss.total_lotto_first_prize DESC, ss.total_lotto_second_prize DESC
            LIMIT 5;
        """)
        for i, row in enumerate(cursor.fetchall(), 1):
            print(f"    {i}. {row[1]} (1등: {row[2]}회, 2등: {row[3]}회)")

        print("\n" + "=" * 60)
        print("✅ store_stats 집계 완료!")
        print("=" * 60)

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
