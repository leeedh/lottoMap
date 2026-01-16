import React, { useState, useMemo } from 'react';
import { Store, LotteryType, FilterState } from '../types';
import StoreCard from './StoreCard';
import { Filter, Trophy, Map, Coffee, X, ChevronDown, MapPin, Medal } from 'lucide-react';

interface SidebarProps {
  stores: Store[]; // Current visible stores on map
  allStores: Store[]; // All filtered stores (for ranking)
  selectedStore: Store | null;
  onSelectStore: (store: Store) => void;
  filters: FilterState;
  onToggleFilter: (type: LotteryType) => void;
  isMobileOpen: boolean;
  onCloseMobile?: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ 
  stores, 
  allStores,
  selectedStore, 
  onSelectStore,
  filters,
  onToggleFilter,
  isMobileOpen,
  onCloseMobile
}) => {
  const [activeTab, setActiveTab] = useState<'map' | 'rank'>('map');
  const [selectedRegion, setSelectedRegion] = useState<string>('전체');
  const [selectedDistrict, setSelectedDistrict] = useState<string>('전체');

  const activeClass = (isActive: boolean, colorClass: string) => 
    isActive 
      ? `${colorClass} text-white shadow-md ring-1 ring-black ring-opacity-5` 
      : 'bg-white text-gray-500 hover:bg-gray-50 border border-gray-200';

  // 1. Extract Unique Regions (Si/Do)
  const regions = useMemo(() => {
    const regionSet = new Set(allStores.map(s => s.address.split(' ')[0]));
    return ['전체', ...Array.from(regionSet).sort()];
  }, [allStores]);

  // 2. Extract Districts based on Selected Region
  const districts = useMemo(() => {
    if (selectedRegion === '전체') return ['전체'];
    const districtSet = new Set(
        allStores
            .filter(s => s.address.startsWith(selectedRegion))
            .map(s => s.address.split(' ')[1])
    );
    return ['전체', ...Array.from(districtSet).sort()];
  }, [allStores, selectedRegion]);

  // 3. Filter for Ranking List
  const rankingStores = useMemo(() => {
    let result = allStores;
    if (selectedRegion !== '전체') {
        result = result.filter(s => s.address.startsWith(selectedRegion));
    }
    if (selectedDistrict !== '전체') {
        result = result.filter(s => s.address.includes(selectedDistrict)); // Simple check
    }
    // Sort by Total Wins (desc)
    return result.sort((a, b) => {
        const totalA = a.wins.lotto1 + a.wins.pension; // 1st prizes weight
        const totalB = b.wins.lotto1 + b.wins.pension;
        return totalB - totalA;
    });
  }, [allStores, selectedRegion, selectedDistrict]);

  // Handle Region Change
  const handleRegionChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedRegion(e.target.value);
    setSelectedDistrict('전체'); // Reset district
  };

  const getRankBadge = (index: number) => {
    if (index === 0) return <Medal size={20} className="text-yellow-400 fill-yellow-400" />;
    if (index === 1) return <Medal size={20} className="text-gray-400 fill-gray-400" />;
    if (index === 2) return <Medal size={20} className="text-orange-400 fill-orange-400" />;
    return <span className="text-sm font-bold text-gray-400 w-5 text-center">{index + 1}</span>;
  };

  return (
    <div className={`
      fixed inset-y-0 left-0 z-[1002] w-full md:w-[400px] bg-white shadow-2xl transform transition-transform duration-300 ease-in-out flex flex-col
      ${isMobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
    `}>
      {/* Header Area */}
      <div className="bg-white z-10 flex-shrink-0 relative shadow-sm">
        <div className="p-6 pb-0">
            {/* Mobile Close Button */}
            <button 
                onClick={onCloseMobile}
                className="md:hidden absolute top-6 right-6 p-2 bg-gray-100 rounded-full text-gray-500 hover:bg-gray-200"
            >
                <X size={20} />
            </button>

            {/* Title */}
            <div className="flex items-center mb-6">
                <div className="bg-gray-900 p-2.5 rounded-xl mr-3 shadow-lg">
                <Trophy className="text-yellow-400" size={24} />
                </div>
                <div>
                <h1 className="text-2xl font-black text-gray-900 tracking-tight leading-none">Lucky Map</h1>
                <p className="text-xs text-gray-500 font-medium mt-1">대한민국 1등 당첨 명당 지도</p>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-gray-200">
                <button
                    onClick={() => setActiveTab('map')}
                    className={`flex-1 pb-3 text-sm font-bold border-b-2 transition-colors flex items-center justify-center ${
                        activeTab === 'map' ? 'border-gray-900 text-gray-900' : 'border-transparent text-gray-400 hover:text-gray-600'
                    }`}
                >
                    <Map size={16} className="mr-2" />
                    지도 내 명당
                </button>
                <button
                    onClick={() => setActiveTab('rank')}
                    className={`flex-1 pb-3 text-sm font-bold border-b-2 transition-colors flex items-center justify-center ${
                        activeTab === 'rank' ? 'border-gray-900 text-gray-900' : 'border-transparent text-gray-400 hover:text-gray-600'
                    }`}
                >
                    <Trophy size={16} className="mr-2" />
                    전체 랭킹
                </button>
            </div>
        </div>
        
        {/* Sub-Header Filters (Dynamic content based on Tab) */}
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-100">
            {activeTab === 'map' ? (
                // MAP TAB FILTERS
                <div className="space-y-3">
                    <div className="flex items-center text-[11px] font-bold text-gray-400 uppercase tracking-wider">
                        <Filter size={10} className="mr-1.5" />
                        복권 종류 필터
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                        <button 
                        onClick={() => onToggleFilter(LotteryType.LOTTO)}
                        className={`py-2 px-3 rounded-lg text-xs font-bold transition-all duration-200 flex items-center justify-center ${activeClass(filters[LotteryType.LOTTO], 'bg-lotto')}`}
                        >
                        <span className={`w-1.5 h-1.5 rounded-full mr-2 ${filters[LotteryType.LOTTO] ? 'bg-white' : 'bg-red-500'}`}></span>
                        로또 6/45
                        </button>
                        <button 
                        onClick={() => onToggleFilter(LotteryType.PENSION)}
                        className={`py-2 px-3 rounded-lg text-xs font-bold transition-all duration-200 flex items-center justify-center ${activeClass(filters[LotteryType.PENSION], 'bg-pension')}`}
                        >
                        <span className={`w-1.5 h-1.5 rounded-full mr-2 ${filters[LotteryType.PENSION] ? 'bg-white' : 'bg-blue-500'}`}></span>
                        연금복권
                        </button>
                    </div>
                </div>
            ) : (
                // RANKING TAB FILTERS
                <div className="space-y-3">
                    <div className="flex items-center text-[11px] font-bold text-gray-400 uppercase tracking-wider">
                        <MapPin size={10} className="mr-1.5" />
                        지역별 순위 검색
                    </div>
                    <div className="flex gap-2">
                        <div className="relative flex-1">
                            <select 
                                value={selectedRegion}
                                onChange={handleRegionChange}
                                className="w-full appearance-none bg-white border border-gray-200 text-gray-700 py-2 px-3 pr-8 rounded-lg text-xs font-bold focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent"
                            >
                                {regions.map(r => <option key={r} value={r}>{r}</option>)}
                            </select>
                            <ChevronDown size={14} className="absolute right-2 top-2.5 text-gray-400 pointer-events-none" />
                        </div>
                        <div className="relative flex-1">
                            <select 
                                value={selectedDistrict}
                                onChange={(e) => setSelectedDistrict(e.target.value)}
                                disabled={selectedRegion === '전체'}
                                className="w-full appearance-none bg-white border border-gray-200 text-gray-700 py-2 px-3 pr-8 rounded-lg text-xs font-bold focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent disabled:bg-gray-100 disabled:text-gray-400"
                            >
                                {districts.map(d => <option key={d} value={d}>{d}</option>)}
                            </select>
                            <ChevronDown size={14} className="absolute right-2 top-2.5 text-gray-400 pointer-events-none" />
                        </div>
                    </div>
                </div>
            )}
        </div>
      </div>

      {/* List Content */}
      <div className="flex-1 overflow-y-auto bg-gray-50 p-4 custom-scrollbar">
        {/* Results Count Header */}
        <div className="mb-4 flex justify-between items-center px-1">
          <h2 className="text-sm font-bold text-gray-800 flex items-center">
            {activeTab === 'map' ? (
                 <>
                    <Map size={14} className="mr-1.5 text-gray-400" />
                    지도 내 명당
                 </>
            ) : (
                <>
                    <Trophy size={14} className="mr-1.5 text-gray-400" />
                    {selectedRegion} {selectedDistrict !== '전체' && selectedDistrict} 랭킹
                </>
            )}
            <span className="ml-1.5 bg-gray-200 text-gray-700 px-2 py-0.5 rounded-md text-xs">
                {activeTab === 'map' ? stores.length : rankingStores.length}
            </span>
          </h2>
          <span className="text-[10px] text-gray-400 bg-white px-2 py-1 rounded-full border border-gray-100 shadow-sm">
            1등 당첨 많은 순
          </span>
        </div>
        
        {/* The List */}
        <div className="space-y-3 pb-4">
          {(activeTab === 'map' ? stores : rankingStores).length > 0 ? (
            (activeTab === 'map' ? stores : rankingStores).map((store, index) => (
               <div key={store.id} className="relative group">
                  {/* Rank Badge for Ranking Tab */}
                  {activeTab === 'rank' && (
                    <div className="absolute -left-2 top-1/2 -translate-y-1/2 z-10 flex flex-col items-center justify-center -ml-2">
                        {getRankBadge(index)}
                    </div>
                  )}
                  
                  <div className={`${activeTab === 'rank' ? 'pl-4' : ''}`}>
                    <StoreCard 
                        store={store} 
                        isSelected={selectedStore?.id === store.id}
                        onClick={() => onSelectStore(store)}
                    />
                  </div>
               </div>
            ))
          ) : (
            <div className="flex flex-col items-center justify-center py-20 text-center opacity-60">
              <Trophy size={48} className="text-gray-300 mb-4" />
              <p className="text-gray-900 font-bold mb-1">조건에 맞는 명당이 없습니다</p>
              <p className="text-xs text-gray-500">
                  {activeTab === 'map' ? '지도를 이동하거나 축소해보세요.' : '다른 지역을 선택해보세요.'}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Footer - Buy Me a Coffee */}
      <div className="p-4 border-t border-gray-100 bg-white z-10 flex-shrink-0 safe-area-bottom">
        <a 
          href="https://www.buymeacoffee.com" 
          target="_blank" 
          rel="noopener noreferrer"
          className="group flex items-center justify-center w-full py-3.5 bg-[#FFDD00] hover:bg-[#FFDD00]/90 text-gray-900 font-bold rounded-xl transition-all shadow-sm hover:shadow-md text-sm"
        >
          <div className="bg-white p-1.5 rounded-full mr-2.5 group-hover:scale-110 transition-transform">
             <Coffee className="text-gray-900" size={16} />
          </div>
          <span>당첨되셨나요? 커피 한 잔 후원하기 ☕️</span>
        </a>
      </div>
    </div>
  );
};

export default Sidebar;