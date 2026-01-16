/// <reference types="vite/client" />

import React, { useEffect, useRef, useState } from 'react';
import { Store, LotteryType, WinStats } from '../types';
import { MAP_CENTER } from '../constants';

// 카카오지도 타입 정의
declare global {
  interface Window {
    kakao: any;
  }
}

interface MapContainerProps {
  stores: Store[];
  selectedStore: Store | null;
  onSelectStore: (store: Store) => void;
  onBoundsChange: (bounds: {
    sw: { lat: number; lng: number };
    ne: { lat: number; lng: number };
  }) => void;
}

// 커스텀 마커 생성 함수
const createCustomMarker = (type: LotteryType, wins: WinStats, store: Store, onClick: () => void) => {
  const totalWins = wins.lotto1 + wins.pension;
  const isHighValue = totalWins >= 3;
  const size = isHighValue ? 40 : 32;
  const iconSize = isHighValue ? 20 : 16;

  let bgColor = '';
  let ringColor = '';
  let iconHtml = '';

  switch (type) {
    case LotteryType.LOTTO:
      bgColor = '#ef4444'; // red-500
      ringColor = '#fecaca'; // red-200
      iconHtml = `<svg xmlns="http://www.w3.org/2000/svg" width="${iconSize}" height="${iconSize}" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/></svg>`;
      break;
    case LotteryType.PENSION:
      bgColor = '#3b82f6'; // blue-500
      ringColor = '#bfdbfe'; // blue-200
      iconHtml = `<svg xmlns="http://www.w3.org/2000/svg" width="${iconSize}" height="${iconSize}" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>`;
      break;
  }

  // DOM 요소 생성 (HTML 문자열 대신)
  const contentElement = document.createElement('div');
  contentElement.style.cssText = `position: relative; display: flex; align-items: center; justify-content: center; width: ${size}px; height: ${size}px; border-radius: 50%; background-color: ${bgColor}; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05); border: 4px solid ${ringColor}; cursor: pointer; transition: transform 0.2s;`;
  contentElement.innerHTML = iconHtml;
  
  // 높은 당첨 횟수인 경우 배지 추가
  if (isHighValue) {
    const badge = document.createElement('span');
    badge.style.cssText = 'position: absolute; top: -8px; right: -8px; background-color: #111827; color: white; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 9999px; border: 2px solid white; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);';
    badge.textContent = String(totalWins);
    contentElement.appendChild(badge);
  }

  // 클릭 이벤트 추가
  contentElement.addEventListener('click', onClick);

  // 커스텀 오버레이 생성
  const customOverlay = new window.kakao.maps.CustomOverlay({
    position: new window.kakao.maps.LatLng(store.lat, store.lng),
    content: contentElement,
    yAnchor: 1,
    zIndex: 1
  });

  return customOverlay;
};

// 인포윈도우 생성 함수
const createInfoWindow = (store: Store) => {
  const infoContent = `
    <div style="min-width: 200px; padding: 12px; font-family: system-ui, -apple-system, sans-serif;">
      <div style="margin-bottom: 12px;">
        <h3 style="font-weight: bold; color: #111827; font-size: 18px; margin-bottom: 4px; margin: 0 0 4px 0;">${store.name}</h3>
        <p style="font-size: 12px; color: #6b7280; margin: 0;">${store.address}</p>
      </div>
      
      <div style="display: flex; justify-content: space-between; background-color: #f9fafb; border-radius: 8px; padding: 8px; margin-bottom: 12px; border: 1px solid #f3f4f6;">
        <div style="display: flex; flex-direction: column; align-items: center; flex: 1;">
          <span style="font-size: 10px; color: #6b7280;">로또1등</span>
          <span style="font-weight: bold; color: #dc2626; font-size: 14px;">${store.wins.lotto1}</span>
        </div>
        <div style="width: 1px; background-color: #e5e7eb; height: 24px; align-self: center; margin: 0 4px;"></div>
        <div style="display: flex; flex-direction: column; align-items: center; flex: 1;">
          <span style="font-size: 10px; color: #6b7280;">로또2등</span>
          <span style="font-weight: bold; color: #ea580c; font-size: 14px;">${store.wins.lotto2}</span>
        </div>
        <div style="width: 1px; background-color: #e5e7eb; height: 24px; align-self: center; margin: 0 4px;"></div>
        <div style="display: flex; flex-direction: column; align-items: center; flex: 1;">
          <span style="font-size: 10px; color: #6b7280;">연금</span>
          <span style="font-weight: bold; color: #2563eb; font-size: 14px;">${store.wins.pension}</span>
        </div>
      </div>

      <div style="border-top: 1px solid #f3f4f6; padding-top: 8px;">
        <p style="font-size: 11px; font-weight: bold; color: #9ca3af; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.05em;">최근 당첨 이력</p>
        <ul style="font-size: 12px; max-height: 120px; overflow-y: auto; list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 6px;">
          ${store.history.map(record => `
            <li style="display: flex; align-items: center; justify-content: space-between; padding-right: 4px;">
              <div style="display: flex; align-items: center;">
                <span style="width: 6px; height: 6px; border-radius: 50%; margin-right: 8px; background-color: ${record.type === LotteryType.LOTTO ? '#ef4444' : '#3b82f6'};"></span>
                <span style="font-weight: 500; color: #374151;">${record.round}회</span>
                <span style="margin-left: 6px; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; ${record.rank === 1 ? 'background-color: #fee2e2; color: #991b1b;' : 'background-color: #ffedd5; color: #9a3412;'}">
                  ${record.rank}등
                  ${record.method ? `<span style="font-weight: normal; margin-left: 2px;">(${record.method})</span>` : ''}
                </span>
              </div>
              <span style="font-size: 10px; color: #9ca3af;">${record.date}</span>
            </li>
          `).join('')}
          ${store.history.length === 0 ? '<li style="text-align: center; color: #9ca3af; font-style: italic; padding: 8px 0;">상세 이력이 없습니다.</li>' : ''}
        </ul>
      </div>
    </div>
  `;

  return new window.kakao.maps.InfoWindow({
    content: infoContent,
    removable: true,
    maxWidth: 300
  });
};

// 한국 지도 범위 정의 (남한 기준)
const KOREA_BOUNDS = {
  minLat: 33.0,   // 제주도 남쪽
  maxLat: 38.6,   // DMZ 북쪽
  minLng: 124.5,  // 서해 섬들
  maxLng: 132.0   // 독도 동쪽
};

const MapContainerComponent: React.FC<MapContainerProps> = ({ 
  stores, 
  selectedStore, 
  onSelectStore, 
  onBoundsChange 
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const markersRef = useRef<any[]>([]);
  const infoWindowsRef = useRef<any[]>([]);
  const [kakaoLoaded, setKakaoLoaded] = useState(false);
  const scriptLoadedRef = useRef(false);
  const lastValidCenterRef = useRef<{ lat: number; lng: number } | null>(null);

  // 카카오지도 API 스크립트 로드
  useEffect(() => {
    // 이미 로드되어 있으면 바로 설정
    if (window.kakao && window.kakao.maps) {
      console.log('카카오지도 API가 이미 로드되어 있습니다.');
      setKakaoLoaded(true);
      return;
    }

    // 이미 스크립트 로드를 시도했다면 중복 방지
    if (scriptLoadedRef.current) {
      console.log('카카오지도 스크립트 로드가 이미 진행 중입니다.');
      return;
    }

    const apiKey = (import.meta.env as any).VITE_KAKAO_MAP_API_KEY as string | undefined;
    
    console.log('카카오지도 API 키 확인:', apiKey ? '설정됨' : '설정되지 않음');
    
    if (!apiKey) {
      console.error('카카오지도 API 키가 설정되지 않았습니다. .env.local 파일에 VITE_KAKAO_MAP_API_KEY를 추가해주세요.');
      return;
    }

    // 이미 같은 스크립트가 있는지 확인
    const existingScript = document.querySelector(`script[src*="dapi.kakao.com"]`);
    if (existingScript) {
      console.log('카카오지도 스크립트가 이미 존재합니다. 로드 대기 중...');
      // 스크립트가 로드될 때까지 대기
      const checkKakao = setInterval(() => {
        if (window.kakao && window.kakao.maps) {
          clearInterval(checkKakao);
          window.kakao.maps.load(() => {
            console.log('카카오지도 API 초기화 완료');
            setKakaoLoaded(true);
          });
        }
      }, 100);
      
      // 최대 10초 대기
      setTimeout(() => {
        clearInterval(checkKakao);
        if (!window.kakao) {
          console.error('카카오지도 스크립트 로드 타임아웃');
        }
      }, 10000);
      
      return;
    }

    scriptLoadedRef.current = true;
    const script = document.createElement('script');
    script.id = 'kakao-map-script';
    script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${apiKey}&autoload=false`;
    script.async = true;
    
    script.onload = () => {
      console.log('카카오지도 스크립트 로드 완료');
      if (window.kakao && window.kakao.maps) {
        window.kakao.maps.load(() => {
          console.log('카카오지도 API 초기화 완료');
          setKakaoLoaded(true);
        });
      } else {
        console.error('카카오지도 API 객체를 찾을 수 없습니다.');
      }
    };

    script.onerror = (error) => {
      console.error('카카오지도 스크립트 로드 실패:', error);
      console.error('스크립트 URL:', script.src.replace(apiKey, '***'));
      console.error('가능한 원인:');
      console.error('1. API 키가 잘못되었거나 유효하지 않습니다.');
      console.error('2. 카카오 개발자 콘솔(https://developers.kakao.com)에서 웹 플랫폼이 등록되지 않았습니다.');
      console.error('3. JavaScript 키를 사용해야 합니다 (REST API 키가 아닌).');
      console.error('4. 도메인이 허용 목록에 등록되지 않았습니다 (localhost는 자동 허용).');
      scriptLoadedRef.current = false;
    };

    document.head.appendChild(script);
  }, []);

  // 지도 초기화
  useEffect(() => {
    if (!kakaoLoaded || !mapContainerRef.current) {
      console.log('지도 초기화 대기 중...', { kakaoLoaded, hasContainer: !!mapContainerRef.current });
      return;
    }

    console.log('지도 초기화 시작');
    const container = mapContainerRef.current;
    
    // 컨테이너 크기 확인
    if (container.offsetWidth === 0 || container.offsetHeight === 0) {
      console.warn('지도 컨테이너 크기가 0입니다. 부모 요소의 크기를 확인해주세요.');
    }
    
    const options = {
      center: new window.kakao.maps.LatLng(MAP_CENTER.lat, MAP_CENTER.lng),
      level: MAP_CENTER.zoom
    };

    let map;
    try {
      map = new window.kakao.maps.Map(container, options);
      mapRef.current = map;
      console.log('지도 생성 완료');
    } catch (error) {
      console.error('지도 생성 실패:', error);
      return;
    }

    // 줌 레벨 범위 제한 (1~13)
    map.setMinLevel(1);
    map.setMaxLevel(13);

    // 줌 컨트롤 제거 (기존 코드와 동일하게)
    // 카카오지도는 기본적으로 줌 컨트롤이 있지만, 제거하려면 CSS로 숨길 수 있습니다.

    // 지도 범위 체크 함수: 한국 지도 범위 내에 있는지 확인
    const isWithinKoreaBounds = (bounds: any): boolean => {
      const sw = bounds.getSouthWest();
      const ne = bounds.getNorthEast();
      
      // 지도의 남서쪽과 북동쪽 모서리가 모두 한국 범위 내에 있어야 함
      const swInBounds = sw.getLat() >= KOREA_BOUNDS.minLat && 
                         sw.getLat() <= KOREA_BOUNDS.maxLat &&
                         sw.getLng() >= KOREA_BOUNDS.minLng && 
                         sw.getLng() <= KOREA_BOUNDS.maxLng;
      
      const neInBounds = ne.getLat() >= KOREA_BOUNDS.minLat && 
                         ne.getLat() <= KOREA_BOUNDS.maxLat &&
                         ne.getLng() >= KOREA_BOUNDS.minLng && 
                         ne.getLng() <= KOREA_BOUNDS.maxLng;
      
      return swInBounds && neInBounds;
    };

    // 지도 이동/줌 변경 이벤트 리스너
    const updateBounds = () => {
      if (!map) return;
      const bounds = map.getBounds();
      const sw = bounds.getSouthWest();
      const ne = bounds.getNorthEast();
      
      onBoundsChange({
        sw: { lat: sw.getLat(), lng: sw.getLng() },
        ne: { lat: ne.getLat(), lng: ne.getLng() }
      });
    };

    // 드래그 종료 시 범위 체크 및 제한
    const handleDragEnd = () => {
      if (!map) return;
      
      const bounds = map.getBounds();
      const center = map.getCenter();
      
      // 한국 범위 내에 있는지 확인
      if (isWithinKoreaBounds(bounds)) {
        // 범위 내에 있으면 현재 중심 좌표를 유효한 위치로 저장
        lastValidCenterRef.current = {
          lat: center.getLat(),
          lng: center.getLng()
        };
        updateBounds();
      } else {
        // 범위를 벗어났으면 이전 유효한 위치로 되돌리기
        if (lastValidCenterRef.current) {
          const validCenter = new window.kakao.maps.LatLng(
            lastValidCenterRef.current.lat,
            lastValidCenterRef.current.lng
          );
          // panTo를 사용하여 부드럽게 되돌리기 (튕기는 효과)
          map.panTo(validCenter);
        } else {
          // 유효한 위치가 없으면 기본 중심으로 되돌리기
          const defaultCenter = new window.kakao.maps.LatLng(MAP_CENTER.lat, MAP_CENTER.lng);
          map.panTo(defaultCenter);
          lastValidCenterRef.current = { lat: MAP_CENTER.lat, lng: MAP_CENTER.lng };
        }
        // bounds 업데이트는 panTo 완료 후 자동으로 호출됨
      }
    };

    window.kakao.maps.event.addListener(map, 'dragend', handleDragEnd);
    window.kakao.maps.event.addListener(map, 'zoom_changed', updateBounds);
    
    // 초기 중심 좌표를 유효한 위치로 저장
    lastValidCenterRef.current = { lat: MAP_CENTER.lat, lng: MAP_CENTER.lng };
    
    // 초기 bounds 전달
    updateBounds();

    // 콘솔에서 지도 정보를 확인할 수 있는 전역 함수 등록
    // 사용법: 콘솔에서 getMapZoom(), getMapScale(), getMapInfo() 호출
    (window as any).getMapZoom = () => {
      if (!mapRef.current) {
        console.warn('지도가 아직 초기화되지 않았습니다.');
        return null;
      }
      const level = mapRef.current.getLevel();
      console.log(`현재 줌 레벨: ${level} (1=가장 넓음, 14=가장 좁음)`);
      return level;
    };

    (window as any).getMapScale = () => {
      if (!mapRef.current) {
        console.warn('지도가 아직 초기화되지 않았습니다.');
        return null;
      }
      const bounds = mapRef.current.getBounds();
      const sw = bounds.getSouthWest();
      const ne = bounds.getNorthEast();
      
      // 위도 차이를 이용한 대략적인 거리 계산 (km)
      const latDiff = ne.getLat() - sw.getLat();
      const lngDiff = ne.getLng() - sw.getLng();
      
      // 위도 1도 ≈ 111km, 경도는 위도에 따라 달라짐
      const latKm = latDiff * 111;
      const lngKm = lngDiff * 111 * Math.cos((sw.getLat() + ne.getLat()) / 2 * Math.PI / 180);
      
      // 대각선 거리 (대략적인 지도 범위)
      const diagonalKm = Math.sqrt(latKm * latKm + lngKm * lngKm);
      
      // 축척 계산 (1:XXXX 형식으로 표시)
      // 화면 크기 대략 800px 기준으로 계산
      const screenWidthPx = 800;
      const scale = Math.round(diagonalKm * 1000 / screenWidthPx);
      
      console.log(`현재 지도 범위: 약 ${diagonalKm.toFixed(2)}km (대각선)`);
      console.log(`대략적인 축척: 1:${scale.toLocaleString()}`);
      console.log(`위도 범위: ${sw.getLat().toFixed(6)} ~ ${ne.getLat().toFixed(6)}`);
      console.log(`경도 범위: ${sw.getLng().toFixed(6)} ~ ${ne.getLng().toFixed(6)}`);
      
      return {
        diagonalKm: diagonalKm,
        scale: scale,
        bounds: {
          sw: { lat: sw.getLat(), lng: sw.getLng() },
          ne: { lat: ne.getLat(), lng: ne.getLng() }
        }
      };
    };

    (window as any).getMapInfo = () => {
      if (!mapRef.current) {
        console.warn('지도가 아직 초기화되지 않았습니다.');
        return null;
      }
      const level = mapRef.current.getLevel();
      const center = mapRef.current.getCenter();
      const bounds = mapRef.current.getBounds();
      const sw = bounds.getSouthWest();
      const ne = bounds.getNorthEast();
      
      const latDiff = ne.getLat() - sw.getLat();
      const lngDiff = ne.getLng() - sw.getLng();
      const latKm = latDiff * 111;
      const lngKm = lngDiff * 111 * Math.cos((sw.getLat() + ne.getLat()) / 2 * Math.PI / 180);
      const diagonalKm = Math.sqrt(latKm * latKm + lngKm * lngKm);
      const screenWidthPx = 800;
      const scale = Math.round(diagonalKm * 1000 / screenWidthPx);
      
      const info = {
        zoomLevel: level,
        center: { lat: center.getLat(), lng: center.getLng() },
        bounds: {
          sw: { lat: sw.getLat(), lng: sw.getLng() },
          ne: { lat: ne.getLat(), lng: ne.getLng() }
        },
        range: {
          diagonalKm: diagonalKm,
          latKm: latKm,
          lngKm: lngKm
        },
        scale: scale
      };
      
      console.log('=== 지도 정보 ===');
      console.log(`줌 레벨: ${level} (1=가장 넓음, 14=가장 좁음)`);
      console.log(`중심 좌표: (${center.getLat().toFixed(6)}, ${center.getLng().toFixed(6)})`);
      console.log(`지도 범위: 약 ${diagonalKm.toFixed(2)}km (대각선)`);
      console.log(`  - 위도 방향: 약 ${latKm.toFixed(2)}km`);
      console.log(`  - 경도 방향: 약 ${lngKm.toFixed(2)}km`);
      console.log(`대략적인 축척: 1:${scale.toLocaleString()}`);
      console.log('================');
      
      return info;
    };

    console.log('콘솔에서 지도 정보 확인 가능:');
    console.log('  - getMapZoom() : 현재 줌 레벨 확인');
    console.log('  - getMapScale() : 현재 축척 및 범위 확인');
    console.log('  - getMapInfo() : 전체 지도 정보 확인');
  }, [kakaoLoaded, onBoundsChange]);

  // 마커 생성 및 업데이트
  useEffect(() => {
    if (!mapRef.current || !kakaoLoaded) return;

    const map = mapRef.current;

    // 기존 마커 및 인포윈도우 제거
    markersRef.current.forEach(marker => marker.setMap(null));
    infoWindowsRef.current.forEach(infoWindow => infoWindow.close());
    markersRef.current = [];
    infoWindowsRef.current = [];

    // 새 마커 생성
    stores.forEach(store => {
      const marker = createCustomMarker(
        store.primaryCategory,
        store.wins,
        store,
        () => {
          onSelectStore(store);
          
          // 인포윈도우 표시
          const infoWindow = createInfoWindow(store);
          infoWindow.open(map, new window.kakao.maps.LatLng(store.lat, store.lng));
          infoWindowsRef.current.push(infoWindow);
        }
      );

      marker.setMap(map);
      markersRef.current.push(marker);
    });
  }, [stores, kakaoLoaded, onSelectStore]);

  // 선택된 스토어로 지도 이동
  useEffect(() => {
    if (!mapRef.current || !selectedStore) return;

    const moveLatLon = new window.kakao.maps.LatLng(selectedStore.lat, selectedStore.lng);
    mapRef.current.setLevel(16);
    mapRef.current.panTo(moveLatLon);
  }, [selectedStore]);

  return (
    <div className="w-full h-full z-0">
      <div ref={mapContainerRef} id="kakao-map" className="w-full h-full" />
    </div>
  );
};

export default MapContainerComponent;
