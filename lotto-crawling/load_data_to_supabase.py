#!/usr/bin/env python3
"""
CSV 데이터를 Supabase에 적재하는 스크립트
DB.md의 변환 규칙에 따라 draws, stores, winning_records 테이블에 데이터를 삽입합니다.
"""
import csv
import hashlib
import os
import sys
from pathlib import Path
from collections import defaultdict

def get_supabase_config():
    """환경변수 또는 .env.local에서 Supabase 설정을 읽어옵니다."""
    config = {}

    # .env.local 파일에서 읽기
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

    # 환경변수에서도 확인 (우선순위 높음)
    supabase_url = os.getenv('VITE_SUPABASE_URL') or config.get('VITE_SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or config.get('SUPABASE_SERVICE_ROLE_KEY')

    return supabase_url, supabase_key


def normalize_method(method_raw: str) -> str:
    """자동수동 값을 정규화합니다."""
    method_map = {
        '자동': 'AUTO',
        '수동': 'MANUAL',
        '반자동': 'SEMI',
    }
    return method_map.get(method_raw.strip(), 'UNKNOWN')


def normalize_rank(rank_raw: str) -> int:
    """등수 값을 정규화합니다."""
    rank_map = {
        '1등': 1,
        '2등': 2,
        '보너스': 0,
    }
    return rank_map.get(rank_raw.strip(), 1)


def normalize_lottery_type(lottery_type_raw: str) -> str:
    """복권종류 값을 정규화합니다."""
    return 'LOTTO' if lottery_type_raw.strip().lower() == 'lotto' else 'PENSION'


def compute_source_row_hash(round_no: int, lottery_type: str, store_source_id: str, rank: int, source_seq: int) -> str:
    """source_row_hash를 계산합니다."""
    hash_input = f"{round_no}|{lottery_type}|{store_source_id}|{rank}|{source_seq or 0}"
    return hashlib.sha256(hash_input.encode()).hexdigest()


def load_csv_data(csv_path: str):
    """CSV 파일을 읽어서 파싱합니다."""
    draws = set()  # round_no 집합
    stores = {}  # source_id -> store_data
    winning_records = []  # 당첨 기록 리스트

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            round_no = int(row['회차'])
            source_id = row['판매점ID'].strip()
            source_seq = int(row['번호']) if row['번호'].strip() else None
            name = row['판매점명'].strip()
            rank_raw = row['등수'].strip()
            method_raw = row['자동수동'].strip()
            address_raw = row['주소'].strip()
            lat_raw = row['위도'].strip()
            lng_raw = row['경도'].strip()
            lottery_type_raw = row['복권종류'].strip()

            # 정규화
            rank = normalize_rank(rank_raw)
            method = normalize_method(method_raw)
            lottery_type = normalize_lottery_type(lottery_type_raw)
            lat = float(lat_raw) if lat_raw else None
            lng = float(lng_raw) if lng_raw else None

            # draws 수집
            draws.add(round_no)

            # stores 수집 (같은 source_id면 가장 최신 정보로 덮어씀)
            if source_id not in stores or stores[source_id]['round_no'] < round_no:
                stores[source_id] = {
                    'source_id': source_id,
                    'name': name,
                    'address_raw': address_raw,
                    'address_norm': address_raw,  # 현재는 동일하게 사용
                    'lat': lat,
                    'lng': lng,
                    'round_no': round_no,  # 최신 정보 판단용 (DB에는 저장 안 함)
                }

            # winning_records 수집
            source_row_hash = compute_source_row_hash(round_no, lottery_type, source_id, rank, source_seq)
            winning_records.append({
                'source_row_hash': source_row_hash,
                'round_no': round_no,  # draw_id로 사용
                'store_source_id': source_id,  # 나중에 store_id로 변환
                'lottery_type': lottery_type,
                'rank': rank,
                'method': method,
                'source_seq': source_seq,
            })

    return sorted(draws), stores, winning_records


def insert_draws(supabase, draws):
    """draws 테이블에 회차 데이터를 삽입합니다."""
    print(f"📌 draws 테이블에 {len(draws)}개 회차 삽입 중...")

    batch_size = 500
    draws_list = [{'round_no': r} for r in draws]

    for i in range(0, len(draws_list), batch_size):
        batch = draws_list[i:i+batch_size]
        supabase.table('draws').upsert(batch, on_conflict='round_no').execute()
        print(f"  ... {min(i+batch_size, len(draws_list))}/{len(draws_list)} 완료")

    print(f"✅ draws 테이블 삽입 완료")


def insert_stores(supabase, stores):
    """stores 테이블에 판매점 데이터를 삽입합니다."""
    print(f"📌 stores 테이블에 {len(stores)}개 판매점 삽입 중...")

    batch_size = 500
    store_list = []
    for store in stores.values():
        store_data = {
            'name': store['name'],
            'address_raw': store['address_raw'],
            'address_norm': store['address_norm'],
            'source_id': store['source_id'],
        }
        if store['lat'] is not None:
            store_data['lat'] = store['lat']
        if store['lng'] is not None:
            store_data['lng'] = store['lng']
        store_list.append(store_data)

    for i in range(0, len(store_list), batch_size):
        batch = store_list[i:i+batch_size]
        supabase.table('stores').upsert(batch, on_conflict='source_id').execute()
        print(f"  ... {min(i+batch_size, len(store_list))}/{len(store_list)} 완료")

    print(f"✅ stores 테이블 삽입 완료")


def get_store_id_map(supabase):
    """source_id -> store.id 매핑을 가져옵니다."""
    print("📌 store_id 매핑 조회 중...")
    store_id_map = {}
    page_size = 1000
    offset = 0

    while True:
        response = supabase.table('stores').select('id, source_id').range(offset, offset + page_size - 1).execute()
        if not response.data:
            break
        for row in response.data:
            store_id_map[row['source_id']] = row['id']
        offset += page_size
        if len(response.data) < page_size:
            break

    print(f"  - {len(store_id_map)}개 매핑 조회 완료")
    return store_id_map


def insert_winning_records(supabase, winning_records, store_id_map):
    """winning_records 테이블에 당첨 기록을 삽입합니다."""
    print(f"📌 winning_records 테이블에 {len(winning_records)}개 기록 삽입 중...")

    batch_size = 500
    skipped = 0
    records_to_insert = []

    for record in winning_records:
        store_id = store_id_map.get(record['store_source_id'])
        if store_id is None:
            skipped += 1
            continue

        record_data = {
            'source_row_hash': record['source_row_hash'],
            'draw_id': record['round_no'],
            'store_id': store_id,
            'lottery_type': record['lottery_type'],
            'rank': record['rank'],
            'method': record['method'],
        }
        if record['source_seq'] is not None:
            record_data['source_seq'] = record['source_seq']
        records_to_insert.append(record_data)

    print(f"  - 삽입할 레코드: {len(records_to_insert)}개, 스킵: {skipped}개")

    for i in range(0, len(records_to_insert), batch_size):
        batch = records_to_insert[i:i+batch_size]
        try:
            supabase.table('winning_records').upsert(batch, on_conflict='source_row_hash').execute()
        except Exception as e:
            print(f"  ⚠️ 배치 {i//batch_size + 1} 오류: {e}")
            # 개별 삽입 시도
            for rec in batch:
                try:
                    supabase.table('winning_records').upsert([rec], on_conflict='source_row_hash').execute()
                except Exception as e2:
                    print(f"    - 레코드 스킵 (hash: {rec['source_row_hash'][:16]}...): {e2}")
        print(f"  ... {min(i+batch_size, len(records_to_insert))}/{len(records_to_insert)} 처리 완료")

    print(f"✅ winning_records 테이블 삽입 완료")


def main():
    """메인 함수"""
    print("=" * 60)
    print("CSV 데이터 → Supabase 적재 스크립트")
    print("=" * 60)

    # Supabase 설정 확인
    supabase_url, supabase_key = get_supabase_config()
    if not supabase_url or not supabase_key:
        print("❌ Supabase 설정을 찾을 수 없습니다.")
        print("\n.env.local 파일에 다음을 추가해주세요:")
        print("  VITE_SUPABASE_URL=https://xxx.supabase.co")
        print("  SUPABASE_SERVICE_ROLE_KEY=eyJ...")
        sys.exit(1)

    # supabase-py import
    try:
        from supabase import create_client, Client
    except ImportError:
        print("❌ supabase 패키지가 설치되지 않았습니다.")
        print("설치: pip3 install supabase")
        sys.exit(1)

    # CSV 파일 경로
    csv_path = Path(__file__).parent / 'all_lottery_stores.csv'
    if not csv_path.exists():
        print(f"❌ CSV 파일을 찾을 수 없습니다: {csv_path}")
        sys.exit(1)

    # CSV 데이터 로드
    print(f"\n📖 CSV 파일 읽는 중: {csv_path}")
    draws, stores, winning_records = load_csv_data(csv_path)
    print(f"  - 회차: {len(draws)}개 (범위: {min(draws)} ~ {max(draws)})")
    print(f"  - 판매점: {len(stores)}개")
    print(f"  - 당첨 기록: {len(winning_records)}개")

    # Supabase 클라이언트 생성
    print(f"\n🔗 Supabase 연결 중...")
    supabase: Client = create_client(supabase_url, supabase_key)
    print(f"  - URL: {supabase_url}")

    try:
        # 1. draws 삽입
        print("\n" + "-" * 40)
        insert_draws(supabase, draws)

        # 2. stores 삽입
        print("\n" + "-" * 40)
        insert_stores(supabase, stores)

        # 3. store_id 매핑 가져오기
        print("\n" + "-" * 40)
        store_id_map = get_store_id_map(supabase)

        # 4. winning_records 삽입
        print("\n" + "-" * 40)
        insert_winning_records(supabase, winning_records, store_id_map)

        print("\n" + "=" * 60)
        print("✅ 모든 데이터 적재 완료!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
