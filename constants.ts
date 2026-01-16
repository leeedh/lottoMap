import { Store, LotteryType, LottoMethod } from './types';

// Helper to generate mock history
const createLottoRecord = (id: string, round: number, rank: number, method: LottoMethod, date: string) => ({
  id: `l-${id}`, type: LotteryType.LOTTO, round, rank, method, date
});

const createPensionRecord = (id: string, round: number, date: string) => ({
  id: `p-${id}`, type: LotteryType.PENSION, round, rank: 1, date
});

export const MOCK_STORES: Store[] = [
  {
    id: '1',
    name: '스파 편의점',
    address: '서울 노원구 동일로 1493',
    lat: 37.6563,
    lng: 127.0624,
    primaryCategory: LotteryType.LOTTO,
    wins: { lotto1: 4, lotto2: 2, pension: 0 },
    history: [
      createLottoRecord('1-1', 1090, 1, LottoMethod.AUTO, '2023.10.21'),
      createLottoRecord('1-2', 1085, 1, LottoMethod.AUTO, '2023.09.16'),
      createLottoRecord('1-3', 1072, 1, LottoMethod.MANUAL, '2023.06.17'),
      createLottoRecord('1-4', 1060, 1, LottoMethod.AUTO, '2023.03.25'),
      createLottoRecord('1-5', 1055, 2, LottoMethod.AUTO, '2023.02.18'),
      createLottoRecord('1-6', 1040, 2, LottoMethod.MANUAL, '2022.11.05'),
    ]
  },
  {
    id: '2',
    name: '부일카서비스',
    address: '부산 동구 자성로133번길 35',
    lat: 35.1388,
    lng: 129.0629,
    primaryCategory: LotteryType.LOTTO,
    wins: { lotto1: 3, lotto2: 3, pension: 0 },
    history: [
      createLottoRecord('2-1', 1100, 1, LottoMethod.AUTO, '2023.12.30'),
      createLottoRecord('2-2', 1095, 1, LottoMethod.SEMI_AUTO, '2023.11.25'),
      createLottoRecord('2-3', 1080, 1, LottoMethod.AUTO, '2023.08.12'),
      createLottoRecord('2-4', 1075, 2, LottoMethod.MANUAL, '2023.07.08'),
      createLottoRecord('2-5', 1070, 2, LottoMethod.AUTO, '2023.06.03'),
      createLottoRecord('2-6', 1065, 2, LottoMethod.AUTO, '2023.04.29'),
    ]
  },
  {
    id: '3',
    name: '인터넷 복권 판매점',
    address: '동행복권 공식 홈페이지',
    lat: 37.4815,
    lng: 127.0125,
    primaryCategory: LotteryType.PENSION,
    wins: { lotto1: 1, lotto2: 5, pension: 4 },
    history: [
      createPensionRecord('3-1', 195, '2024.01.04'),
      createPensionRecord('3-2', 190, '2023.11.30'),
      createPensionRecord('3-3', 188, '2023.11.16'),
      createPensionRecord('3-4', 180, '2023.09.21'),
      createLottoRecord('3-5', 1099, 1, LottoMethod.MANUAL, '2023.12.23'),
      createLottoRecord('3-6', 1098, 2, LottoMethod.MANUAL, '2023.12.16'),
    ]
  },
  {
    id: '4',
    name: '잠실매점',
    address: '서울 송파구 올림픽로 269',
    lat: 37.5147,
    lng: 127.1005,
    primaryCategory: LotteryType.LOTTO,
    wins: { lotto1: 2, lotto2: 1, pension: 0 },
    history: [
      createLottoRecord('4-1', 1050, 1, LottoMethod.AUTO, '2023.01.14'),
      createLottoRecord('4-2', 1045, 1, LottoMethod.AUTO, '2022.12.10'),
      createLottoRecord('4-3', 1041, 2, LottoMethod.MANUAL, '2022.11.12'),
    ]
  },
  {
    id: '6',
    name: '목화휴게소',
    address: '경남 사천시 용현면 주문리 4',
    lat: 34.9912,
    lng: 128.0531,
    primaryCategory: LotteryType.LOTTO,
    wins: { lotto1: 2, lotto2: 4, pension: 0 },
    history: [
      createLottoRecord('6-1', 1088, 1, LottoMethod.AUTO, '2023.10.07'),
      createLottoRecord('6-2', 1030, 1, LottoMethod.AUTO, '2022.08.27'),
      createLottoRecord('6-3', 1025, 2, LottoMethod.MANUAL, '2022.07.23'),
      createLottoRecord('6-4', 1020, 2, LottoMethod.AUTO, '2022.06.18'),
    ]
  },
  {
    id: '7',
    name: '로또명당 대구점',
    address: '대구 달서구 월배로 100',
    lat: 35.8242,
    lng: 128.5375,
    primaryCategory: LotteryType.LOTTO,
    wins: { lotto1: 1, lotto2: 2, pension: 0 },
    history: [
      createLottoRecord('7-1', 1052, 1, LottoMethod.MANUAL, '2023.01.28'),
      createLottoRecord('7-2', 1048, 2, LottoMethod.AUTO, '2022.12.31'),
    ]
  },
  {
    id: '9',
    name: '행운드림 복권방',
    address: '경기 성남시 분당구 판교로 300',
    lat: 37.4011,
    lng: 127.1098,
    primaryCategory: LotteryType.PENSION,
    wins: { lotto1: 0, lotto2: 1, pension: 3 },
    history: [
      createPensionRecord('9-1', 185, '2023.10.26'),
      createPensionRecord('9-2', 170, '2023.07.13'),
      createPensionRecord('9-3', 165, '2023.06.08'),
      createLottoRecord('9-4', 1082, 2, LottoMethod.MANUAL, '2023.08.26'),
    ]
  },
  {
    id: '15',
    name: '강남 페이퍼',
    address: '서울 강남구 테헤란로 152',
    lat: 37.5000,
    lng: 127.0355,
    primaryCategory: LotteryType.PENSION,
    wins: { lotto1: 0, lotto2: 2, pension: 2 },
    history: [
      createPensionRecord('15-1', 175, '2023.08.17'),
      createPensionRecord('15-2', 160, '2023.05.04'),
      createLottoRecord('15-3', 1080, 2, LottoMethod.AUTO, '2023.08.12'),
    ]
  }
];

export const MAP_CENTER = {
  lat: 36.5,
  lng: 127.8,
  zoom: 7
};