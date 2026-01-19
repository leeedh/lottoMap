#!/usr/bin/env python3
"""
winning_records 테이블의 won_at을 draws 테이블의 draw_date로 업데이트하는 스크립트
"""
import os
import sys
from pathlib import Path

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


def main():
    print("=" * 60)
    print("winning_records 테이블 won_at 업데이트")
    print("=" * 60)

    supabase_url, supabase_key = get_supabase_config()
    if not supabase_url or not supabase_key:
        print("Supabase 설정을 찾을 수 없습니다.")
        sys.exit(1)

    from supabase import create_client
    supabase = create_client(supabase_url, supabase_key)

    # 1. draws 테이블에서 round_no -> draw_date 매핑 조회
    print("\n📖 draws 테이블에서 draw_date 매핑 조회 중...")
    draw_date_map = {}
    offset = 0
    page_size = 1000

    while True:
        response = supabase.table('draws').select('round_no, draw_date').range(offset, offset + page_size - 1).execute()
        if not response.data:
            break
        for row in response.data:
            draw_date_map[row['round_no']] = row['draw_date']
        offset += page_size
        if len(response.data) < page_size:
            break

    print(f"  - {len(draw_date_map)}개 회차 매핑 조회 완료")

    # 2. winning_records 조회 및 업데이트
    print("\n📖 winning_records 테이블 조회 중...")
    all_records = []
    offset = 0

    while True:
        response = supabase.table('winning_records').select('source_row_hash, draw_id').range(offset, offset + page_size - 1).execute()
        if not response.data:
            break
        all_records.extend(response.data)
        offset += page_size
        print(f"  ... {len(all_records)}개 조회됨")
        if len(response.data) < page_size:
            break

    print(f"  - 총 {len(all_records)}개 레코드 조회 완료")

    # 3. won_at 업데이트 (draw_id별로 그룹화하여 일괄 업데이트)
    print("\n📌 won_at 업데이트 중...")

    # draw_id별로 그룹화
    from collections import defaultdict
    records_by_draw = defaultdict(list)
    for record in all_records:
        records_by_draw[record['draw_id']].append(record['source_row_hash'])

    total_draws = len(records_by_draw)
    updated_count = 0

    for i, (draw_id, hashes) in enumerate(records_by_draw.items(), 1):
        draw_date = draw_date_map.get(draw_id)
        if draw_date:
            # draw_id 기준으로 won_at 일괄 업데이트
            supabase.table('winning_records')\
                .update({'won_at': draw_date})\
                .eq('draw_id', draw_id)\
                .execute()
            updated_count += len(hashes)

        if i % 100 == 0 or i == total_draws:
            print(f"  ... {i}/{total_draws} 회차 처리 완료 ({updated_count}개 레코드)")

    print(f"\n✅ won_at 업데이트 완료!")

    # 검증
    print("\n📋 검증 (최근 로또 1등 당첨 5건):")
    sample = supabase.table('winning_records')\
        .select('draw_id, won_at, lottery_type, rank, stores(name)')\
        .eq('lottery_type', 'LOTTO')\
        .eq('rank', 1)\
        .order('draw_id', desc=True)\
        .limit(5)\
        .execute()

    for rec in sample.data:
        store = rec.get('stores', {})
        print(f"  - {rec['draw_id']}회차 ({rec['won_at']}): {store.get('name', 'N/A')}")

    print("\n" + "=" * 60)
    print("완료!")
    print("=" * 60)


if __name__ == '__main__':
    main()
