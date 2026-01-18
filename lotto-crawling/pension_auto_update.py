"""
연금복권720+ 당첨 판매점 자동 갱신 스크립트

새로운 회차가 발표되면 자동으로 감지하여 기존 CSV에 추가합니다.

사용법:
    python pension_auto_update.py                    # 새 회차 확인 및 수집
    python pension_auto_update.py --watch            # 새 회차 감지될 때까지 대기 (폴링)
    python pension_auto_update.py --watch --interval 600  # 10분마다 확인
"""

import asyncio
import argparse
import csv
import os
from datetime import datetime
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup


# 설정
DEFAULT_CSV_FILE = "pension_all_rounds.csv"
DEFAULT_POLL_INTERVAL = 600  # 10분
MAX_POLL_DURATION = 12 * 3600  # 최대 12시간 대기


class PensionAutoUpdater:
    """연금복권720+ 데이터 자동 갱신"""

    def __init__(self, csv_file: str = DEFAULT_CSV_FILE):
        self.csv_file = csv_file
        self.url = "https://www.dhlottery.co.kr/wnprchsplcsrch/home"
        self.lottery_code = "pt720"
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def start_browser(self, max_retries: int = 3):
        """브라우저 시작 (세션 유지, 재시도 포함)"""
        if self.browser:
            return  # 이미 시작됨

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    print(f"🔄 브라우저 시작 재시도 ({attempt + 1}/{max_retries})...")
                    await asyncio.sleep(3)

                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(headless=False)
                self.context = await self.browser.new_context()
                self.page = await self.context.new_page()

                # 페이지 로드 (타임아웃 증가)
                await self.page.goto(self.url, wait_until="domcontentloaded", timeout=90000)
                await self.page.wait_for_selector('.store-list', state='visible', timeout=30000)
                print("✅ 브라우저 시작 완료")
                return

            except Exception as e:
                print(f"⚠️ 브라우저 시작 실패 (시도 {attempt + 1}): {e}")
                await self.close_browser()

        raise Exception("브라우저 시작 실패 (최대 재시도 횟수 초과)")

    async def close_browser(self):
        """브라우저 종료"""
        if self.context:
            await self.context.close()
            self.context = None
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
        self.page = None

    def get_local_latest_round(self) -> int:
        """로컬 CSV에서 최신 회차 확인"""
        if not os.path.exists(self.csv_file):
            print(f"⚠️  CSV 파일이 없습니다: {self.csv_file}")
            return 0

        with open(self.csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rounds = [int(row['회차']) for row in reader if row.get('회차')]

        if not rounds:
            return 0

        latest = max(rounds)
        print(f"📁 로컬 최신 회차: {latest}회")
        return latest

    async def get_site_latest_round(self) -> int:
        """동행복권 사이트에서 최신 회차 확인 (기존 브라우저 세션 사용)"""
        try:
            # 연금복권720+ 선택
            await self.page.select_option('select#ltGds', self.lottery_code)
            await asyncio.sleep(2)

            # 셀렉터가 로드될 때까지 대기
            await self.page.wait_for_selector('select#srchLtEpsd', state='visible', timeout=10000)

            # 첫 번째 옵션이 최신 회차
            first_option = await self.page.query_selector('select#srchLtEpsd option:first-child')
            if first_option:
                value = await first_option.get_attribute('value')
                latest = int(value)
                print(f"🌐 사이트 최신 회차: {latest}회")
                return latest
            return 0

        except Exception as e:
            import traceback
            print(f"❌ 사이트 확인 실패: {type(e).__name__}: {e}")
            traceback.print_exc()
            return 0

    async def crawl_round(self, round_num: int) -> list:
        """특정 회차 크롤링 (기존 브라우저 세션 사용)"""
        print(f"\n🔄 {round_num}회 크롤링 중...")

        try:
            # 연금복권720+ 선택
            await self.page.select_option('select#ltGds', self.lottery_code)
            await asyncio.sleep(1)

            # 회차 선택
            await self.page.select_option('select#srchLtEpsd', str(round_num))
            await self.page.evaluate('WnPrchsPlcSrchM.fn_selectWnShp()')
            await asyncio.sleep(2)
            await self.page.wait_for_selector('.store-box', state='visible', timeout=15000)

            # 데이터 추출
            html = await self.page.content()
            soup = BeautifulSoup(html, 'html.parser')
            stores = self._extract_stores(soup, str(round_num))

            print(f"✅ {round_num}회: {len(stores)}개 판매점 수집")
            return stores

        except Exception as e:
            print(f"❌ {round_num}회 크롤링 실패: {e}")
            return []

    def _extract_stores(self, soup: BeautifulSoup, round_num: str) -> list:
        """HTML에서 판매점 정보 추출"""
        stores = []
        store_boxes = soup.select('.store-box')

        for store_box in store_boxes:
            try:
                store_id = store_box.get('data-ltshpid', '')
                store_name_elem = store_box.select_one('.store-loc')
                store_name = store_name_elem.text.strip() if store_name_elem else ''

                if not store_id or not store_name:
                    continue

                store_num_elem = store_box.select_one('.store-num')
                store_num = store_num_elem.text.strip() if store_num_elem else ''

                rank_elem = store_box.select_one('.draw-rank')
                rank = rank_elem.text.strip() if rank_elem else ''

                opt_elem = store_box.select_one('.draw-opt')
                opt = opt_elem.text.strip() if opt_elem else ''

                addr_elem = store_box.select_one('.store-addr')
                address = addr_elem.text.strip() if addr_elem else ''

                tel_elem = store_box.select_one('.store-tel')
                phone = tel_elem.text.strip() if tel_elem else ''

                lottery_types = []
                for badge in store_box.select('.txt-bagge'):
                    lottery_types.append(badge.text.strip())

                lat_input = store_box.select_one('input.shpLat')
                lon_input = store_box.select_one('input.shpLot')
                latitude = lat_input.get('value', '') if lat_input else ''
                longitude = lon_input.get('value', '') if lon_input else ''

                region_elem = store_box.select_one('.tit-detail')
                region = ''
                if region_elem:
                    region_text = region_elem.text.strip()
                    region = region_text.split('(')[0].strip()

                store_info = {
                    '회차': round_num,
                    '판매점ID': store_id,
                    '번호': store_num,
                    '판매점명': store_name,
                    '등수': rank,
                    '자동수동': opt,
                    '지역': region,
                    '주소': address,
                    '전화번호': phone,
                    '취급복권': ', '.join(lottery_types),
                    '위도': latitude,
                    '경도': longitude,
                    '크롤링시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                stores.append(store_info)
            except:
                continue

        return stores

    def append_to_csv(self, stores: list):
        """기존 CSV에 새 데이터 추가"""
        if not stores:
            print("⚠️  추가할 데이터가 없습니다.")
            return

        file_exists = os.path.exists(self.csv_file)

        with open(self.csv_file, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=stores[0].keys())
            if not file_exists:
                writer.writeheader()
            writer.writerows(stores)

        print(f"💾 {len(stores)}개 데이터가 {self.csv_file}에 추가되었습니다.")

    async def check_and_update(self) -> bool:
        """새 회차 확인 및 업데이트"""
        print("\n" + "="*50)
        print(f"🔍 연금복권720+ 새 회차 확인 중... ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
        print("="*50)

        local_latest = self.get_local_latest_round()

        try:
            # 브라우저 시작
            await self.start_browser()

            site_latest = await self.get_site_latest_round()

            if site_latest == 0:
                print("❌ 사이트 확인 실패")
                return False

            if site_latest <= local_latest:
                print(f"\n✅ 이미 최신 상태입니다. (로컬: {local_latest}회, 사이트: {site_latest}회)")
                return False

            # 새 회차 발견
            new_rounds = list(range(local_latest + 1, site_latest + 1))
            print(f"\n🆕 새 회차 발견: {new_rounds}")

            # 새 회차들 크롤링
            all_new_stores = []
            for round_num in new_rounds:
                stores = await self.crawl_round(round_num)
                all_new_stores.extend(stores)
                await asyncio.sleep(2)  # 서버 부담 감소

            # CSV에 추가
            if all_new_stores:
                self.append_to_csv(all_new_stores)
                print(f"\n🎉 업데이트 완료! {len(new_rounds)}개 회차, {len(all_new_stores)}개 판매점 추가")
                return True
            else:
                print("\n⚠️  새 데이터를 수집하지 못했습니다.")
                return False

        finally:
            # 브라우저 종료
            await self.close_browser()

    async def watch_and_update(self, interval: int = DEFAULT_POLL_INTERVAL):
        """새 회차가 감지될 때까지 대기 후 업데이트"""
        print("\n" + "="*60)
        print("👀 연금복권720+ 새 회차 감지 모드 시작")
        print(f"   - 확인 간격: {interval}초 ({interval//60}분)")
        print(f"   - 최대 대기: {MAX_POLL_DURATION//3600}시간")
        print("   - 종료: Ctrl+C")
        print("="*60)

        start_time = datetime.now()
        attempt = 0

        while True:
            attempt += 1
            elapsed = (datetime.now() - start_time).total_seconds()

            if elapsed > MAX_POLL_DURATION:
                print(f"\n⏰ 최대 대기 시간 초과 ({MAX_POLL_DURATION//3600}시간)")
                break

            print(f"\n[시도 {attempt}] {datetime.now().strftime('%H:%M:%S')}")

            try:
                updated = await self.check_and_update()
                if updated:
                    print("\n✅ 업데이트 완료! 감지 모드 종료.")
                    break
            except Exception as e:
                print(f"❌ 오류 발생: {e}")

            print(f"⏳ {interval}초 후 다시 확인...")
            await asyncio.sleep(interval)


async def main():
    parser = argparse.ArgumentParser(description='연금복권720+ 당첨 판매점 자동 갱신')
    parser.add_argument('--csv', type=str, default=DEFAULT_CSV_FILE,
                        help=f'CSV 파일 경로 (기본값: {DEFAULT_CSV_FILE})')
    parser.add_argument('--watch', action='store_true',
                        help='새 회차 감지 모드 (폴링)')
    parser.add_argument('--interval', type=int, default=DEFAULT_POLL_INTERVAL,
                        help=f'확인 간격 (초, 기본값: {DEFAULT_POLL_INTERVAL})')

    args = parser.parse_args()

    updater = PensionAutoUpdater(csv_file=args.csv)

    if args.watch:
        await updater.watch_and_update(interval=args.interval)
    else:
        await updater.check_and_update()


if __name__ == "__main__":
    asyncio.run(main())
