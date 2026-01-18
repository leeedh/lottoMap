"""
연금복권720+ 당첨 판매점 크롤링 스크립트

동행복권 사이트에서 연금복권720+ 당첨 판매점 정보를 수집합니다.
- 회차별, 등수별, 지역별 필터링 가능
- CSV 파일로 저장
"""

import asyncio
import csv
from datetime import datetime
from typing import List, Dict
from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup


class PensionLotteryCrawler:
    """연금복권720+ 당첨 판매점 크롤러"""

    def __init__(self, headless: bool = True):
        """
        초기화

        Args:
            headless: 브라우저를 숨김 모드로 실행할지 여부 (True: 숨김, False: 보임)
        """
        self.url = "https://www.dhlottery.co.kr/wnprchsplcsrch/home"
        self.headless = headless
        self.browser: Browser = None
        self.page: Page = None
        self.lottery_code = "pt720"  # 연금복권720+ 코드

    async def start(self):
        """브라우저 시작"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)

        # 실제 브라우저처럼 보이도록 컨텍스트 설정
        context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="ko-KR",
        )
        self.page = await context.new_page()

        # domcontentloaded로 변경하고 타임아웃 증가
        await self.page.goto(self.url, wait_until="domcontentloaded", timeout=60000)
        print(f"✅ 페이지 로드 완료: {self.url}")

        # 페이지가 완전히 로드될 때까지 대기
        await self.page.wait_for_selector('.store-list', state='visible', timeout=30000)

        # 연금복권720+ 선택
        await self.select_lottery_type()

    async def close(self):
        """브라우저 종료"""
        if self.browser:
            await self.browser.close()
            print("🔒 브라우저 종료")

    async def select_lottery_type(self):
        """연금복권720+ 선택"""
        await self.page.select_option('select#ltGds', self.lottery_code)
        await asyncio.sleep(2)  # 데이터 로드 대기
        print("✅ 복권 종류 선택: 연금복권720+")

    async def select_round(self, round_num: str):
        """
        회차 선택

        Args:
            round_num: 회차 번호 (예: "250")
        """
        # 회차 선택 드롭다운
        await self.page.select_option('select#srchLtEpsd', round_num)
        # JavaScript 함수 호출하여 데이터 갱신
        await self.page.evaluate('WnPrchsPlcSrchM.fn_selectWnShp()')
        await asyncio.sleep(1)  # 데이터 로드 대기
        # 데이터가 로드될 때까지 대기
        await self.page.wait_for_selector('.store-box', state='visible', timeout=10000)
        print(f"✅ 회차 선택: {round_num}회")

    async def select_rank(self, rank: str):
        """
        등수 선택

        Args:
            rank: 등수 ("전체", "1등", "2등", "보너스")
        """
        rank_map = {
            "전체": "all",
            "1등": "1",
            "2등": "2",
            "보너스": "B"  # 연금복권 보너스
        }

        if rank in rank_map:
            value = rank_map[rank]
            # 등수 탭 버튼 클릭
            await self.page.click(f'#srchLtWnRank li[value="{value}"] button')
            await asyncio.sleep(2)  # 데이터 로드 대기
            print(f"✅ 등수 선택: {rank}")
        else:
            print(f"⚠️  지원하지 않는 등수: {rank}")

    async def get_stores(self) -> List[Dict]:
        """
        현재 페이지의 판매점 정보 추출

        Returns:
            판매점 정보 리스트
        """
        # 페이지 HTML 가져오기
        html = await self.page.content()
        soup = BeautifulSoup(html, 'html.parser')

        stores = []
        store_boxes = soup.select('.store-box')

        for store_box in store_boxes:
            try:
                # 기본 정보 추출
                store_id = store_box.get('data-ltshpid', '')

                # 판매점 이름
                store_name_elem = store_box.select_one('.store-loc')
                store_name = store_name_elem.text.strip() if store_name_elem else ''

                # 필수 정보가 없으면 건너뛰기
                if not store_id or not store_name:
                    continue

                # 번호
                store_num_elem = store_box.select_one('.store-num')
                store_num = store_num_elem.text.strip() if store_num_elem else ''

                # 등수
                rank_elem = store_box.select_one('.draw-rank')
                rank = rank_elem.text.strip() if rank_elem else ''

                # 자동/수동 (선택적)
                opt_elem = store_box.select_one('.draw-opt')
                opt = opt_elem.text.strip() if opt_elem else ''

                # 주소
                addr_elem = store_box.select_one('.store-addr')
                address = addr_elem.text.strip() if addr_elem else ''

                # 전화번호
                tel_elem = store_box.select_one('.store-tel')
                phone = tel_elem.text.strip() if tel_elem else ''

                # 취급 복권 종류
                lottery_types = []
                for badge in store_box.select('.txt-bagge'):
                    lottery_types.append(badge.text.strip())

                # Hidden input에서 좌표 정보 추출
                lat_input = store_box.select_one('input.shpLat')
                lon_input = store_box.select_one('input.shpLot')

                latitude = lat_input.get('value', '') if lat_input else ''
                longitude = lon_input.get('value', '') if lon_input else ''

                # 지역 정보 (tit-detail에서 추출)
                region_elem = store_box.select_one('.tit-detail')
                region = ''
                if region_elem:
                    region_text = region_elem.text.strip()
                    # (숫자) 부분 제거
                    region = region_text.split('(')[0].strip()

                store_info = {
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

            except Exception as e:
                print(f"⚠️  판매점 정보 추출 중 오류: {e}")
                continue

        print(f"✅ {len(stores)}개 판매점 정보 추출 완료")
        return stores

    async def get_available_rounds(self) -> List[str]:
        """
        사용 가능한 회차 목록 조회

        Returns:
            회차 번호 리스트 (최신순)
        """
        options = await self.page.query_selector_all('select#srchLtEpsd option')
        rounds = []
        for option in options:
            value = await option.get_attribute('value')
            if value:
                rounds.append(value)
        return rounds

    async def get_stores_silent(self) -> List[Dict]:
        """로그 없이 판매점 정보 추출"""
        html = await self.page.content()
        soup = BeautifulSoup(html, 'html.parser')

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

    def save_to_csv(self, stores: List[Dict], filename: str = None):
        """
        판매점 정보를 CSV 파일로 저장

        Args:
            stores: 판매점 정보 리스트
            filename: 저장할 파일명 (기본값: pension_stores_YYYYMMDD_HHMMSS.csv)
        """
        if not stores:
            print("⚠️  저장할 데이터가 없습니다.")
            return

        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"pension_stores_{timestamp}.csv"

        # CSV 파일로 저장
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=stores[0].keys())
            writer.writeheader()
            writer.writerows(stores)

        print(f"💾 파일 저장 완료: {filename}")


class ParallelPensionCrawler:
    """병렬 처리를 지원하는 연금복권 크롤러"""

    def __init__(self, max_workers: int = 3):
        """
        초기화

        Args:
            max_workers: 동시 실행할 브라우저 수 (기본값: 3, 권장: 2-5)
        """
        self.max_workers = max_workers
        self.url = "https://www.dhlottery.co.kr/wnprchsplcsrch/home"
        self.lottery_code = "pt720"

    async def _create_browser_context(self, playwright):
        """브라우저 컨텍스트 생성"""
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="ko-KR",
        )
        return browser, context

    def _extract_stores(self, soup: BeautifulSoup, round_num: str) -> List[Dict]:
        """BeautifulSoup에서 판매점 정보 추출"""
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

    async def crawl_all_rounds(self, start_round: int = 1, end_round: int = None,
                                save_interval: int = 100) -> List[Dict]:
        """
        전체 회차 크롤링 (단일 브라우저 순차 처리)

        Args:
            start_round: 시작 회차 (기본값: 1)
            end_round: 종료 회차 (기본값: None = 최신 회차까지)
            save_interval: 중간 저장 간격 (기본값: 100회차마다)

        Returns:
            전체 판매점 정보 리스트
        """
        print("\n" + "="*60)
        print("🚀 연금복권720+ 전체 회차 크롤링 시작")
        print("="*60)

        # 브라우저 시작 (재시도 로직 포함)
        print("\n📋 브라우저 시작 중...")
        playwright = await async_playwright().start()
        browser = None
        page = None

        for attempt in range(3):
            try:
                if attempt > 0:
                    print(f"🔄 브라우저 시작 재시도 ({attempt + 1}/3)...")
                    await asyncio.sleep(5)

                browser, context = await self._create_browser_context(playwright)
                page = await context.new_page()
                await page.goto(self.url, wait_until="domcontentloaded", timeout=120000)
                await page.wait_for_selector('.store-list', state='visible', timeout=60000)
                print("✅ 페이지 로드 완료")
                break
            except Exception as e:
                print(f"⚠️ 페이지 로드 실패 (시도 {attempt + 1}): {e}")
                if browser:
                    await browser.close()
                if attempt == 2:
                    await playwright.stop()
                    raise Exception("브라우저 시작 실패 (최대 재시도 횟수 초과)")

        try:

            # 연금복권720+ 선택
            await page.select_option('select#ltGds', self.lottery_code)

            # 회차 드롭다운이 실제 숫자 값으로 로드될 때까지 대기
            for wait_attempt in range(30):  # 최대 30초 대기
                await asyncio.sleep(1)
                round_values = await page.evaluate('''() => {
                    const select = document.querySelector('select#srchLtEpsd');
                    if (!select) return [];
                    return Array.from(select.options).map(opt => opt.value).filter(v => v && /^\\d+$/.test(v));
                }''')
                if round_values and len(round_values) > 0:
                    break
                if wait_attempt == 29:
                    print("⚠️ 회차 드롭다운 로드 대기 시간 초과")

            print("✅ 연금복권720+ 선택 완료")

            # 최신 회차 확인
            if end_round is None:
                # JavaScript로 직접 옵션 값 가져오기
                round_values = await page.evaluate('''() => {
                    const select = document.querySelector('select#srchLtEpsd');
                    if (!select) return [];
                    return Array.from(select.options).map(opt => opt.value).filter(v => v && /^\\d+$/.test(v));
                }''')

                if round_values and len(round_values) > 0:
                    end_round = int(round_values[0])
                else:
                    # 폴백: DOM에서 직접 확인
                    options = await page.query_selector_all('select#srchLtEpsd option')
                    for option in options:
                        value = await option.get_attribute('value')
                        if value and value.isdigit():
                            end_round = int(value)
                            break

                if end_round is None:
                    # 디버그: 현재 HTML 저장
                    html = await page.content()
                    with open('pension_debug.html', 'w', encoding='utf-8') as f:
                        f.write(html)
                    raise Exception("최신 회차를 찾을 수 없습니다 (pension_debug.html 확인)")
                print(f"   최신 회차: {end_round}회")

            # 크롤링할 회차 목록 생성
            all_rounds = [str(r) for r in range(start_round, end_round + 1)]
            total_rounds = len(all_rounds)

            print(f"\n📊 크롤링 설정:")
            print(f"   - 회차 범위: {start_round}회 ~ {end_round}회 (총 {total_rounds}개)")
            print(f"   - 예상 소요시간: 약 {(total_rounds * 2.5 + (total_rounds // 50) * 10) // 60}분")

            # 결과 저장용
            results = []
            failed_rounds = []
            start_time = datetime.now()

            print("\n🔄 크롤링 진행 중...")

            for i, round_num in enumerate(all_rounds):
                try:
                    await page.select_option('select#srchLtEpsd', round_num)
                    await page.evaluate('WnPrchsPlcSrchM.fn_selectWnShp()')
                    await asyncio.sleep(2)  # 안정적인 2초 대기
                    await page.wait_for_selector('.store-box', state='visible', timeout=15000)

                    html = await page.content()
                    soup = BeautifulSoup(html, 'html.parser')
                    stores = self._extract_stores(soup, round_num)
                    results.extend(stores)

                    # 진행 상황 출력
                    if (i + 1) % 10 == 0 or i == 0:
                        pct = (i + 1) / total_rounds * 100
                        elapsed = (datetime.now() - start_time).total_seconds()
                        eta = (elapsed / (i + 1)) * (total_rounds - i - 1)
                        print(f"   진행: {i+1}/{total_rounds} ({pct:.1f}%) | "
                              f"판매점: {len(results)}개 | 예상 남은 시간: {eta/60:.1f}분")

                    # 중간 저장
                    if save_interval and (i + 1) % save_interval == 0:
                        temp_filename = f"pension_checkpoint_{i+1}.csv"
                        self.save_to_csv(results, temp_filename)
                        print(f"   💾 중간 저장: {temp_filename}")

                    # 50회차마다 추가 휴식 (서버 부담 감소)
                    if (i + 1) % 50 == 0:
                        print(f"   ⏸️  잠시 휴식 중... (10초)")
                        await asyncio.sleep(10)

                except Exception as e:
                    failed_rounds.append(round_num)
                    if len(failed_rounds) <= 5:
                        print(f"   ⚠️ {round_num}회 실패: {e}")
                    await asyncio.sleep(3)  # 실패 시 추가 대기

            end_time = datetime.now()
            elapsed = (end_time - start_time).total_seconds()

            print(f"\n\n✅ 크롤링 완료!")
            print(f"   - 총 소요시간: {elapsed/60:.1f}분 ({elapsed:.0f}초)")
            print(f"   - 수집된 판매점: {len(results)}개")
            print(f"   - 성공 회차: {total_rounds - len(failed_rounds)}개")
            print(f"   - 실패 회차: {len(failed_rounds)}개")

            if failed_rounds:
                print(f"   - 실패 회차 목록: {failed_rounds[:10]}{'...' if len(failed_rounds) > 10 else ''}")

            return results

        finally:
            await browser.close()
            await playwright.stop()

    def save_to_csv(self, stores: List[Dict], filename: str = None):
        """CSV 파일로 저장"""
        if not stores:
            print("⚠️  저장할 데이터가 없습니다.")
            return

        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"pension_all_rounds_{timestamp}.csv"

        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=stores[0].keys())
            writer.writeheader()
            writer.writerows(stores)

        print(f"💾 파일 저장 완료: {filename}")


async def main():
    """메인 실행 함수 - 사용 예제"""

    # 크롤러 생성 (headless=False로 설정하면 브라우저가 보임)
    crawler = PensionLotteryCrawler(headless=False)

    try:
        # 브라우저 시작
        await crawler.start()

        print("\n" + "="*60)
        print("🎰 연금복권720+ 당첨 판매점 크롤링 시작")
        print("="*60 + "\n")

        # 사용 가능한 회차 목록 조회
        rounds = await crawler.get_available_rounds()
        print(f"📋 사용 가능한 회차: {rounds[0]}회 ~ {rounds[-1]}회 (총 {len(rounds)}개)")

        # 최신 회차 크롤링
        latest_round = rounds[0]
        print(f"\n📊 최신 회차 ({latest_round}회) 크롤링")
        await crawler.select_round(latest_round)
        stores = await crawler.get_stores()
        crawler.save_to_csv(stores, f"pension_stores_{latest_round}.csv")

        print("\n" + "="*60)
        print("✅ 크롤링 완료!")
        print("="*60)

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

    finally:
        # 브라우저 종료
        await crawler.close()


if __name__ == "__main__":
    # 이벤트 루프 실행
    asyncio.run(main())
