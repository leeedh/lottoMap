#!/usr/bin/env python3
"""
draws 테이블의 draw_date를 계산하여 업데이트하는 스크립트
로또 6/45: 2002년 12월 7일(토) 1회차 시작, 매주 토요일 추첨
"""
import os
import sys
from pathlib import Path
from datetime import date, timedelta

# 로또 1회차 추첨일 (2002년 12월 7일 토요일)
LOTTO_FIRST_DRAW_DATE = date(2002, 12, 7)


def get_supabase_config():
    """환경변수 또는 .env.local에서 Supabase 설정을 읽어옵니다."""
    config = {}

    env_file = Path(__file__).parent.parent / '.env.local'
    if env_file.exists():
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip().strip('"').strip("'")
        except PermissionError:
            pass

    supabase_url = os.getenv('VITE_SUPABASE_URL') or config.get('VITE_SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or config.get('SUPABASE_SERVICE_ROLE_KEY')

    return supabase_url, supabase_key


def calculate_draw_date(round_no: int) -> date:
    """회차 번호로 추첨일을 계산합니다."""
    # n회차 추첨일 = 1회차 추첨일 + (n-1) * 7일
    return LOTTO_FIRST_DRAW_DATE + timedelta(weeks=round_no - 1)


def main():
    print("=" * 60)
    print("draws 테이블 draw_date 업데이트")
    print("=" * 60)

    supabase_url, supabase_key = get_supabase_config()
    if not supabase_url or not supabase_key:
        print("Supabase 설정을 찾을 수 없습니다.")
        sys.exit(1)

    from supabase import create_client
    supabase = create_client(supabase_url, supabase_key)

    # 모든 회차 조회
    print("\n📖 draws 테이블 조회 중...")
    all_draws = []
    offset = 0
    page_size = 1000

    while True:
        response = supabase.table('draws').select('round_no').range(offset, offset + page_size - 1).execute()
        if not response.data:
            break
        all_draws.extend(response.data)
        offset += page_size
        if len(response.data) < page_size:
            break

    print(f"  - 총 {len(all_draws)}개 회차 조회 완료")

    # draw_date 계산 및 업데이트
    print("\n📌 draw_date 업데이트 중...")
    batch_size = 500
    updates = []

    for draw in all_draws:
        round_no = draw['round_no']
        draw_date = calculate_draw_date(round_no)
        updates.append({
            'round_no': round_no,
            'draw_date': draw_date.isoformat()
        })

    for i in range(0, len(updates), batch_size):
        batch = updates[i:i+batch_size]
        supabase.table('draws').upsert(batch, on_conflict='round_no').execute()
        print(f"  ... {min(i+batch_size, len(updates))}/{len(updates)} 완료")

    print(f"\n✅ draw_date 업데이트 완료!")

    # 검증
    print("\n📋 검증 (샘플 데이터):")
    samples = [1, 100, 500, 1000, 1207]
    for round_no in samples:
        result = supabase.table('draws').select('round_no, draw_date').eq('round_no', round_no).execute()
        if result.data:
            d = result.data[0]
            expected = calculate_draw_date(round_no)
            print(f"  - {d['round_no']}회차: {d['draw_date']} (예상: {expected.isoformat()})")

    print("\n" + "=" * 60)
    print("완료!")
    print("=" * 60)


if __name__ == '__main__':
    main()
