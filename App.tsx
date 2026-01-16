import React, { useState, useMemo } from 'react';
import { MOCK_STORES } from './constants';
import Sidebar from './components/Sidebar';
import MapContainerComponent from './components/MapContainer';
import { LotteryType, Store, FilterState } from './types';
import { Menu, Map as MapIcon, Coffee, List, Check } from 'lucide-react';

// 카카오지도 bounds 타입
interface KakaoMapBounds {
  sw: { lat: number; lng: number };
  ne: { lat: number; lng: number };
}

const App: React.FC = () => {
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [selectedStore, setSelectedStore] = useState<Store | null>(null);
  const [mapBounds, setMapBounds] = useState<KakaoMapBounds | null>(null);
  
  // Initial filter state
  const [filters, setFilters] = useState<FilterState>({
    [LotteryType.LOTTO]: true,
    [LotteryType.PENSION]: true,
  });

  const handleToggleFilter = (type: LotteryType) => {
    setFilters(prev => ({ ...prev, [type]: !prev[type] }));
  };

  const handleSelectStore = (store: Store) => {
    // Toggle logic: If clicking the currently selected store, deselect it.
    if (selectedStore?.id === store.id) {
      setSelectedStore(null);
    } else {
      setSelectedStore(store);
    }
  };

  // 1. Filtered by Type (Lotto / Pension) - Used for Map Markers and Ranking
  // FIX: Filter strictly by primaryCategory to match marker colors with buttons.
  // Previous logic based on 'wins' caused confusion because stores with mixed wins (e.g. Pension store with Lotto win)
  // would show up even if the Pension filter was off, showing a Blue marker when only Red (Lotto) was expected.
  const typeFilteredStores = useMemo(() => {
    return MOCK_STORES.filter(store => {
      if (store.primaryCategory === LotteryType.LOTTO) {
        return filters[LotteryType.LOTTO];
      }
      if (store.primaryCategory === LotteryType.PENSION) {
        return filters[LotteryType.PENSION];
      }
      return false;
    });
  }, [filters]);

  // 2. Filtered by Map Bounds (Visible Stores) - Used for Sidebar Map Tab
  const visibleStores = useMemo(() => {
    if (!mapBounds) return typeFilteredStores;

    return typeFilteredStores.filter(store => {
        // 카카오지도 bounds 체크: sw(남서쪽)와 ne(북동쪽) 좌표 사이에 있는지 확인
        return store.lat >= mapBounds.sw.lat && 
               store.lat <= mapBounds.ne.lat &&
               store.lng >= mapBounds.sw.lng && 
               store.lng <= mapBounds.ne.lng;
    }).sort((a, b) => {
      // Sort visible stores by total wins
      const totalA = a.wins.lotto1 + a.wins.pension + a.wins.lotto2;
      const totalB = b.wins.lotto1 + b.wins.pension + b.wins.lotto2;
      return totalB - totalA;
    });
  }, [typeFilteredStores, mapBounds]);

  const activeFilterClass = (isActive: boolean, type: LotteryType) => {
      const base = "px-4 py-2 rounded-full shadow-md text-xs font-bold flex items-center transition-all active:scale-95 border";
      if (!isActive) return `${base} bg-white text-gray-500 border-gray-200`;
      
      if (type === LotteryType.LOTTO) return `${base} bg-lotto text-white border-red-600 ring-2 ring-red-100`;
      return `${base} bg-pension text-white border-blue-600 ring-2 ring-blue-100`;
  };

  return (
    <div className="flex h-screen w-full bg-gray-100 overflow-hidden relative">
      
      {/* Sidebar (Desktop: Left Panel, Mobile: Full Screen Drawer) */}
      <Sidebar 
        stores={visibleStores} // Only visible stores for 'Map' tab
        allStores={typeFilteredStores} // All stores for 'Ranking' tab
        selectedStore={selectedStore}
        onSelectStore={handleSelectStore}
        filters={filters}
        onToggleFilter={handleToggleFilter}
        isMobileOpen={isMobileOpen}
        onCloseMobile={() => setIsMobileOpen(false)}
      />

      {/* Main Content (Map) */}
      <div className="flex-1 h-full w-full relative md:ml-[400px]">
        <MapContainerComponent 
          stores={typeFilteredStores} // Map needs to know about all valid stores to render markers
          selectedStore={selectedStore}
          onSelectStore={handleSelectStore}
          onBoundsChange={setMapBounds}
        />

        {/* --- MOBILE UI OVERLAYS --- */}
        
        {/* 1. Mobile Header Area */}
        <div className="md:hidden absolute top-0 left-0 right-0 z-[500] pointer-events-none flex flex-col items-center">
            {/* Top Bar */}
            <div className="w-full flex justify-between items-start p-4 bg-gradient-to-b from-white/80 to-transparent">
                {/* Logo / Title Card */}
                <div className="pointer-events-auto bg-white/95 backdrop-blur shadow-sm rounded-xl p-3 border border-gray-100/50">
                    <h1 className="text-lg font-black text-gray-900 leading-none tracking-tight">Lucky Map</h1>
                    <p className="text-[10px] text-gray-500 mt-0.5 font-medium">대한민국 로또/연금 명당</p>
                </div>

                {/* Coffee Button (Small) */}
                <a 
                  href="https://www.buymeacoffee.com" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="pointer-events-auto bg-[#FFDD00] p-2.5 rounded-full shadow-lg hover:scale-105 transition-transform border border-yellow-400"
                  aria-label="Buy me a coffee"
                >
                    <Coffee className="text-gray-900 w-5 h-5" strokeWidth={2.5} />
                </a>
            </div>

            {/* Floating Filter Chips */}
            <div className="flex gap-2 pointer-events-auto mt-[-10px]">
                <button 
                    onClick={() => handleToggleFilter(LotteryType.LOTTO)} 
                    className={activeFilterClass(filters[LotteryType.LOTTO], LotteryType.LOTTO)}
                >
                    {filters[LotteryType.LOTTO] && <Check size={12} className="mr-1" />}
                    로또 6/45
                </button>
                <button 
                    onClick={() => handleToggleFilter(LotteryType.PENSION)} 
                    className={activeFilterClass(filters[LotteryType.PENSION], LotteryType.PENSION)}
                >
                    {filters[LotteryType.PENSION] && <Check size={12} className="mr-1" />}
                    연금복권
                </button>
            </div>
        </div>

        {/* 2. Mobile Bottom Floating Button (List Toggle) */}
        <div className="md:hidden absolute bottom-8 left-0 right-0 z-[500] flex justify-center pointer-events-none safe-area-bottom">
            <button 
                onClick={() => setIsMobileOpen(true)}
                className="pointer-events-auto flex items-center bg-gray-900 text-white pl-5 pr-6 py-3.5 rounded-full shadow-xl hover:bg-gray-800 transition-all active:scale-95 group"
            >
                <List className="mr-2.5 w-5 h-5 group-hover:-translate-y-0.5 transition-transform" />
                <span className="font-bold text-sm tracking-wide">명당 리스트 보기</span>
                <span className="ml-2 bg-gray-700 text-[10px] px-1.5 py-0.5 rounded-full text-gray-200">
                    {visibleStores.length}
                </span>
            </button>
        </div>

        {/* Mobile Overlay Background (Closes sidebar when clicked) */}
        {isMobileOpen && (
          <div 
            className="md:hidden fixed inset-0 bg-black/60 backdrop-blur-sm z-[1001]"
            onClick={() => setIsMobileOpen(false)}
          />
        )}
      </div>
    </div>
  );
};

export default App;