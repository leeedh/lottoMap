#!/usr/bin/env python3
"""
draws 테이블 스키마 마이그레이션
- lottery_type 컬럼 추가
- PK를 (round_no, lottery_type) 복합키로 변경
- 연금복권 회차 데이터 추가
- winning_records FK 수정

실행 전 .env.local에 DATABASE_URL 추가 필요:
DATABASE_URL=postgresql://postgres.[project-ref]:[password]@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres
"""
import os
import sys
from pathlib import Path
from datetime import date, timedelta

# 로또 1회차: 2002년 12월 7일 (토)
LOTTO_FIRST_DRAW_DATE = date(2002, 12, 7)
# 연금복권 720+ 1회차: 2020년 4월 2일 (목)
PENSION_FIRST_DRAW_DATE = date(2020, 4, 2)


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


def calculate_lotto_draw_date(round_no: int) -> date:
    """로또 회차 번호로 추첨일을 계산합니다."""
    return LOTTO_FIRST_DRAW_DATE + timedelta(weeks=round_no - 1)


def calculate_pension_draw_date(round_no: int) -> date:
    """연금복권 회차 번호로 추첨일을 계산합니다."""
    return PENSION_FIRST_DRAW_DATE + timedelta(weeks=round_no - 1)


def main():
    print("=" * 60)
    print("draws 테이블 스키마 마이그레이션")
    print("=" * 60)

    database_url = get_database_url()
    if not database_url:
        print("❌ DATABASE_URL 환경변수를 찾을 수 없습니다.")
        print("\n.env.local 파일에 다음을 추가해주세요:")
        print("  DATABASE_URL=postgresql://postgres.[project-ref]:[password]@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres")
        print("\nSupabase 대시보드 > Settings > Database > Connection string 에서 확인 가능합니다.")
        sys.exit(1)

    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    except ImportError:
        print("❌ psycopg2가 설치되지 않았습니다.")
        print("설치: pip install psycopg2-binary")
        sys.exit(1)

    print(f"\n🔗 데이터베이스 연결 중...")
    conn = psycopg2.connect(database_url)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    try:
        # Step 1: 기존 FK 제약조건 삭제
        print("\n" + "-" * 40)
        print("Step 1: 기존 FK 제약조건 삭제")
        cursor.execute("""
            ALTER TABLE winning_records
            DROP CONSTRAINT IF EXISTS winning_records_draw_id_fkey;
        """)
        print("  ✅ winning_records FK 삭제 완료")

        cursor.execute("""
            ALTER TABLE store_name_history
            DROP CONSTRAINT IF EXISTS store_name_history_drw_no_fkey;
        """)
        print("  ✅ store_name_history FK 삭제 완료")

        # Step 2: draws 테이블에 lottery_type 컬럼 추가
        print("\n" + "-" * 40)
        print("Step 2: draws 테이블에 lottery_type 컬럼 추가")
        cursor.execute("""
            ALTER TABLE draws
            ADD COLUMN IF NOT EXISTS lottery_type VARCHAR(10) NOT NULL DEFAULT 'LOTTO'
            CHECK (lottery_type IN ('LOTTO', 'PENSION'));
        """)
        print("  ✅ lottery_type 컬럼 추가 완료")

        # Step 3: 기존 PK 삭제 및 새 복합 PK 생성
        print("\n" + "-" * 40)
        print("Step 3: PK를 (round_no, lottery_type) 복합키로 변경")
        cursor.execute("""
            ALTER TABLE draws DROP CONSTRAINT IF EXISTS draws_pkey;
        """)
        cursor.execute("""
            ALTER TABLE draws ADD PRIMARY KEY (round_no, lottery_type);
        """)
        print("  ✅ 복합 PK 생성 완료")

        # Step 4: 연금복권 회차 데이터 추가 (1 ~ 298)
        print("\n" + "-" * 40)
        print("Step 4: 연금복권 회차 데이터 추가")
        pension_rounds = []
        for round_no in range(1, 299):  # 1 ~ 298
            draw_date = calculate_pension_draw_date(round_no)
            pension_rounds.append((round_no, 'PENSION', draw_date))

        cursor.executemany("""
            INSERT INTO draws (round_no, lottery_type, draw_date)
            VALUES (%s, %s, %s)
            ON CONFLICT (round_no, lottery_type) DO UPDATE SET draw_date = EXCLUDED.draw_date;
        """, pension_rounds)
        print(f"  ✅ 연금복권 {len(pension_rounds)}개 회차 추가 완료")

        # Step 5: winning_records FK 재설정 (복합 FK)
        print("\n" + "-" * 40)
        print("Step 5: winning_records FK 재설정")
        cursor.execute("""
            ALTER TABLE winning_records
            ADD CONSTRAINT winning_records_draw_fkey
            FOREIGN KEY (draw_id, lottery_type) REFERENCES draws(round_no, lottery_type);
        """)
        print("  ✅ winning_records FK 재설정 완료")

        # Step 6: winning_records won_at 업데이트 (연금복권)
        print("\n" + "-" * 40)
        print("Step 6: winning_records won_at 업데이트 (연금복권)")
        cursor.execute("""
            UPDATE winning_records wr
            SET won_at = d.draw_date
            FROM draws d
            WHERE wr.draw_id = d.round_no
              AND wr.lottery_type = d.lottery_type
              AND wr.lottery_type = 'PENSION';
        """)
        print(f"  ✅ 연금복권 won_at 업데이트 완료")

        # 검증
        print("\n" + "-" * 40)
        print("검증:")
        cursor.execute("SELECT lottery_type, COUNT(*) FROM draws GROUP BY lottery_type;")
        for row in cursor.fetchall():
            print(f"  - {row[0]}: {row[1]}개 회차")

        cursor.execute("""
            SELECT lottery_type, COUNT(*), MIN(won_at), MAX(won_at)
            FROM winning_records
            GROUP BY lottery_type;
        """)
        print("\nwinning_records won_at 범위:")
        for row in cursor.fetchall():
            print(f"  - {row[0]}: {row[1]}건, {row[2]} ~ {row[3]}")

        # 샘플 데이터
        print("\n연금복권 샘플 (최근 1등 당첨 5건):")
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
        print("✅ 마이그레이션 완료!")
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
