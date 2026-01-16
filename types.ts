export enum LotteryType {
  LOTTO = 'LOTTO',
  PENSION = 'PENSION',
}

export enum LottoMethod {
  AUTO = '자동',
  MANUAL = '수동',
  SEMI_AUTO = '반자동',
}

export interface WinRecord {
  id: string;
  type: LotteryType;
  round: number; // 회차
  rank: number; // 등수 (1 or 2 for Lotto, 1 for Pension)
  method?: LottoMethod; // 로또인 경우만 존재
  date: string;
}

export interface WinStats {
  lotto1: number;
  lotto2: number;
  pension: number;
}

export interface Store {
  id: string;
  name: string;
  address: string;
  lat: number;
  lng: number;
  wins: WinStats;
  history: WinRecord[]; // 당첨 근거 데이터
  primaryCategory: LotteryType;
}

export interface FilterState {
  [LotteryType.LOTTO]: boolean;
  [LotteryType.PENSION]: boolean;
}