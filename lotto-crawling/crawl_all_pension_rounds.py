"""
전체 회차 연금복권720+ 당첨 판매점 크롤링 스크립트

1회부터 최신 회차까지 모든 당첨 판매점 정보를 수집합니다.

사용법:
    python crawl_all_pension_rounds.py                    # 전체 회차 크롤링
    python crawl_all_pension_rounds.py --start 100       # 100회부터 크롤링
    python crawl_all_pension_rounds.py --start 100 --end 150  # 100~150회 크롤링
    python crawl_all_pension_rounds.py --workers 5       # 워커 5개로 크롤링
"""

import asyncio
import argparse
from pension_crawler import ParallelPensionCrawler


async def main():
    parser = argparse.ArgumentParser(description='전체 회차 연금복권720+ 당첨 판매점 크롤링')
    parser.add_argument('--start', type=int, default=1, help='시작 회차 (기본값: 1)')
    parser.add_argument('--end', type=int, default=None, help='종료 회차 (기본값: 최신 회차)')
    parser.add_argument('--workers', type=int, default=3, help='병렬 워커 수 (기본값: 3, 권장: 2-5)')
    parser.add_argument('--output', type=str, default='pension_all_rounds.csv', help='출력 파일명')

    args = parser.parse_args()

    print("\n" + "="*60)
    print("🎰 연금복권720+ 전체 회차 크롤러")
    print("="*60)
    print(f"\n설정:")
    print(f"  - 시작 회차: {args.start}회")
    print(f"  - 종료 회차: {args.end if args.end else '최신 회차'}")
    print(f"  - 병렬 워커: {args.workers}개")
    print(f"  - 출력 파일: {args.output}")

    # 병렬 크롤러 생성
    crawler = ParallelPensionCrawler(max_workers=args.workers)

    # 전체 회차 크롤링
    all_stores = await crawler.crawl_all_rounds(
        start_round=args.start,
        end_round=args.end
    )

    # CSV 저장
    if all_stores:
        crawler.save_to_csv(all_stores, args.output)

        # 통계 출력
        print("\n" + "="*60)
        print("📊 크롤링 통계")
        print("="*60)

        # 회차별 통계
        from collections import Counter
        round_counter = Counter([store['회차'] for store in all_stores])
        print(f"\n회차별 판매점 수 (상위 10개):")
        for round_num, count in round_counter.most_common(10):
            print(f"  - {round_num}회: {count}개")

        # 지역별 통계
        region_counter = Counter([store['지역'] for store in all_stores if store['지역']])
        print(f"\n지역별 판매점 수:")
        for region, count in region_counter.most_common():
            print(f"  - {region}: {count}개")

        # 등수별 통계
        rank_counter = Counter([store['등수'] for store in all_stores if store['등수']])
        print(f"\n등수별 통계:")
        for rank, count in rank_counter.most_common():
            print(f"  - {rank}: {count}개")

    print("\n" + "="*60)
    print("✅ 완료!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
