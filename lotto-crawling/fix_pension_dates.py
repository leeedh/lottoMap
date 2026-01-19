#!/usr/bin/env python3
"""
연금복권 추첨일 수정 스크립트
1회차: 2020년 5월 7일 (목), 매주 목요일 추첨
"""
import os
import sys
from pathlib import Path
from datetime import date, timedelta

# 연금복권 720+ 1회차: 2020년 5월 7일 (목) - 298회차가 2026-01-15 기준 역산
PENSION_FIRST_DRAW_DATE = date(2020, 5, 7)


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


def calculate_pension_draw_date(round_no: int) -> date:
    """연금복권 회차 번호로 추첨일을 계산합니다."""
    return PENSION_FIRST_DRAW_DATE + timedelta(weeks=round_no - 1)


def main():
    print("=" * 60)
    print("연금복권 추첨일 수정")
    print(f"1회차 기준일: {PENSION_FIRST_DRAW_DATE} (목)")
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
        # Step 1: draws 테이블의 연금복권 draw_date 업데이트
        print("\n" + "-" * 40)
        print("Step 1: draws 테이블 연금복권 draw_date 업데이트")

        cursor.execute("SELECT round_no FROM draws WHERE lottery_type = 'PENSION' ORDER BY round_no;")
        pension_rounds = [row[0] for row in cursor.fetchall()]
        print(f"  - 연금복권 회차: {len(pension_rounds)}개")

        updates = []
        for round_no in pension_rounds:
            draw_date = calculate_pension_draw_date(round_no)
            updates.append((draw_date, round_no))

        cursor.executemany("""
            UPDATE draws SET draw_date = %s
            WHERE round_no = %s AND lottery_type = 'PENSION';
        """, updates)
        print(f"  ✅ draws 테이블 업데이트 완료")

        # Step 2: winning_records 테이블의 연금복권 won_at 업데이트
        print("\n" + "-" * 40)
        print("Step 2: winning_records 테이블 연금복권 won_at 업데이트")

        cursor.execute("""
            UPDATE winning_records wr
            SET won_at = d.draw_date
            FROM draws d
            WHERE wr.draw_id = d.round_no
              AND wr.lottery_type = d.lottery_type
              AND wr.lottery_type = 'PENSION';
        """)
        print(f"  ✅ winning_records 테이블 업데이트 완료")

        # 검증
        print("\n" + "-" * 40)
        print("검증:")

        # draws 샘플
        print("\ndraws 테이블 (연금복권 샘플):")
        cursor.execute("""
            SELECT round_no, draw_date
            FROM draws
            WHERE lottery_type = 'PENSION' AND round_no IN (1, 100, 200, 298)
            ORDER BY round_no;
        """)
        for row in cursor.fetchall():
            expected = calculate_pension_draw_date(row[0])
            status = "✅" if str(row[1]) == str(expected) else "❌"
            print(f"  {status} {row[0]}회차: {row[1]} (예상: {expected})")

        # winning_records 범위
        print("\nwinning_records won_at 범위:")
        cursor.execute("""
            SELECT lottery_type, COUNT(*), MIN(won_at), MAX(won_at)
            FROM winning_records
            GROUP BY lottery_type
            ORDER BY lottery_type;
        """)
        for row in cursor.fetchall():
            print(f"  - {row[0]}: {row[1]}건, {row[2]} ~ {row[3]}")

        # 연금복권 최근 당첨
        print("\n연금복권 최근 1등 당첨 5건:")
        cursor.execute("""
            SELECT wr.draw_id, wr.won_at, s.name
            FROM winning_records wr
            JOIN stores s ON wr.store_id = s.id
            WHERE wr.lottery_type = 'PENSION' AND wr.rank = 1
            ORDER BY wr.draw_id DESC
            LIMIT 5;
        """)
        for row in cursor.fetchall():
            print(f"  - {row[0]}회차 ({row[1]}): {row[2]}")

        print("\n" + "=" * 60)
        print("✅ 수정 완료!")
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
