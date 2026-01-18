"""
간단한 로또 판매점 크롤링 예제

이 스크립트는 가장 기본적인 사용 예제를 보여줍니다.
"""

import asyncio
from lotto_crawler import LottoStoreCrawler


async def simple_crawl():
    """
    간단한 크롤링 예제
    - 로또 6/45
    - 최신 회차 (기본값)
    - 전체 등수
    """
    print("🎰 로또 당첨 판매점 크롤링 시작\n")
    
    # 크롤러 생성 (브라우저 보이도록 설정)
    crawler = LottoStoreCrawler(headless=False)
    
    try:
        # 1. 브라우저 시작
        print("1️⃣ 브라우저 시작 중...")
        await crawler.start()
        
        # 2. 복권 종류 선택 (로또 6/45)
        print("2️⃣ 로또 6/45 선택...")
        await crawler.select_lottery_type("로또6/45")
        
        # 3. 회차 선택 (1206회)
        print("3️⃣ 1206회 선택...")
        await crawler.select_round("1206")
        
        # 4. 등수 선택 (전체)
        print("4️⃣ 전체 등수 선택...")
        await crawler.select_rank("전체")
        
        # 5. 판매점 정보 수집
        print("5️⃣ 판매점 정보 수집 중...\n")
        stores = await crawler.get_stores()
        
        # 6. 결과 출력
        print(f"\n✅ 총 {len(stores)}개 판매점 정보를 수집했습니다!")
        
        # 상위 3개 판매점 정보 미리보기
        if stores:
            print("\n📋 수집된 판매점 정보 미리보기 (상위 3개):")
            print("-" * 80)
            for i, store in enumerate(stores[:3], 1):
                print(f"\n[{i}] {store['판매점명']}")
                print(f"    등수: {store['등수']} {store['자동수동']}")
                print(f"    주소: {store['주소']}")
                print(f"    전화: {store['전화번호']}")
                print(f"    복권: {store['취급복권']}")
        
        # 7. CSV 파일로 저장
        print("\n6️⃣ CSV 파일로 저장 중...")
        crawler.save_to_csv(stores, "lotto_stores_simple.csv")
        
        print("\n" + "="*80)
        print("🎉 크롤링 완료! 'lotto_stores_simple.csv' 파일을 확인하세요.")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 브라우저 종료
        await crawler.close()


async def crawl_first_prize_only():
    """
    1등 당첨 판매점만 수집하는 예제
    """
    print("🏆 1등 당첨 판매점만 수집합니다\n")
    
    crawler = LottoStoreCrawler(headless=False)
    
    try:
        await crawler.start()
        
        # 로또 6/45, 1206회, 1등만 선택
        await crawler.select_lottery_type("로또6/45")
        await crawler.select_round("1206")
        await crawler.select_rank("1등")
        
        # 데이터 수집
        stores = await crawler.get_stores()
        
        print(f"\n🎰 1등 당첨 판매점: {len(stores)}곳")
        
        # 결과 출력
        if stores:
            print("\n🏆 1등 당첨 판매점 목록:")
            print("-" * 80)
            for i, store in enumerate(stores, 1):
                print(f"\n[{i}] {store['판매점명']}")
                print(f"    지역: {store['지역']}")
                print(f"    주소: {store['주소']}")
                print(f"    자동/수동: {store['자동수동']}")
        
        # CSV 저장
        crawler.save_to_csv(stores, "lotto_first_prize_only.csv")
        print("\n💾 'lotto_first_prize_only.csv' 파일에 저장되었습니다.")
        
    finally:
        await crawler.close()


async def crawl_all_regions():
    """
    모든 지역의 판매점 정보를 수집하는 예제
    ⚠️ 주의: 시간이 오래 걸릴 수 있습니다 (2-3분)
    """
    print("🌏 모든 지역의 판매점 정보를 수집합니다")
    print("⚠️  이 작업은 2-3분 정도 소요될 수 있습니다.\n")
    
    crawler = LottoStoreCrawler(headless=True)  # 백그라운드에서 실행
    
    try:
        await crawler.start()
        
        # 로또 6/45 선택
        await crawler.select_lottery_type("로또6/45")
        await crawler.select_round("1206")
        await crawler.select_rank("전체")
        
        # 모든 지역 크롤링
        all_stores = await crawler.get_all_regions_stores()
        
        # 통계 정보 출력
        print(f"\n📊 수집 통계:")
        print(f"   - 총 판매점 수: {len(all_stores)}곳")
        
        # 지역별 통계
        from collections import Counter
        region_counter = Counter([store['지역'] for store in all_stores if store['지역']])
        print(f"   - 지역별 판매점 수:")
        for region, count in region_counter.most_common():
            print(f"     • {region}: {count}곳")
        
        # CSV 저장
        crawler.save_to_csv(all_stores, "lotto_stores_all_regions.csv")
        print("\n💾 'lotto_stores_all_regions.csv' 파일에 저장되었습니다.")
        
    finally:
        await crawler.close()


async def crawl_all_rounds_quick():
    """
    전체 회차 병렬 크롤링 예제 (최근 10회차만 테스트)
    """
    from lotto_crawler import ParallelLottoCrawler

    print("🚀 전체 회차 크롤링 (테스트: 최근 10회차)\n")

    crawler = ParallelLottoCrawler(max_workers=3)

    # 테스트로 최근 10회차만 크롤링
    all_stores = await crawler.crawl_all_rounds(start_round=1197, end_round=1206)

    if all_stores:
        crawler.save_to_csv(all_stores, "lotto_recent_10_rounds.csv")
        print(f"\n📊 총 {len(all_stores)}개 판매점 정보 수집 완료!")


def main():
    """
    메인 함수 - 실행할 예제를 선택하세요
    """
    print("\n" + "="*80)
    print("🎰 로또 당첨 판매점 크롤러 - 간단한 예제")
    print("="*80 + "\n")

    print("실행할 예제를 선택하세요:")
    print("1. 기본 크롤링 (로또 6/45, 1206회, 전체 등수)")
    print("2. 1등 당첨 판매점만 수집")
    print("3. 모든 지역 판매점 수집 (시간 오래 걸림)")
    print("4. 전체 회차 크롤링 테스트 (최근 10회차)")
    print("5. 전체 회차 크롤링 (1회 ~ 최신회차) ⚠️ 약 20-30분 소요")

    choice = input("\n번호를 입력하세요 (1-5): ").strip()

    if choice == "1":
        asyncio.run(simple_crawl())
    elif choice == "2":
        asyncio.run(crawl_first_prize_only())
    elif choice == "3":
        confirm = input("⚠️  모든 지역을 크롤링하면 2-3분 소요됩니다. 계속하시겠습니까? (y/n): ").strip().lower()
        if confirm == 'y':
            asyncio.run(crawl_all_regions())
        else:
            print("취소되었습니다.")
    elif choice == "4":
        asyncio.run(crawl_all_rounds_quick())
    elif choice == "5":
        confirm = input("⚠️  전체 회차 크롤링은 약 20-30분 소요됩니다. 계속하시겠습니까? (y/n): ").strip().lower()
        if confirm == 'y':
            from lotto_crawler import crawl_all_rounds_example
            asyncio.run(crawl_all_rounds_example())
        else:
            print("취소되었습니다.")
    else:
        print("❌ 잘못된 선택입니다. 1-5 사이의 숫자를 입력하세요.")


if __name__ == "__main__":
    main()

