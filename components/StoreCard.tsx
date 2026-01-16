import React from 'react';
import { Store, LotteryType, LottoMethod } from '../types';
import { MapPin, Trophy, Star, Award, CheckCircle2, ChevronDown } from 'lucide-react';

interface StoreCardProps {
  store: Store;
  isSelected: boolean;
  onClick: () => void;
}

const StoreCard: React.FC<StoreCardProps> = ({ store, isSelected, onClick }) => {
  const getBorderColor = (type: LotteryType) => {
    switch (type) {
      case LotteryType.LOTTO: return 'border-l-lotto';
      case LotteryType.PENSION: return 'border-l-pension';
      default: return 'border-l-gray-300';
    }
  };

  const getBadgeColor = (type: LotteryType) => {
    switch (type) {
      case LotteryType.LOTTO: return 'bg-red-50 text-red-700 border border-red-100';
      case LotteryType.PENSION: return 'bg-blue-50 text-blue-700 border border-blue-100';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div 
      onClick={onClick}
      className={`
        w-full p-4 bg-white rounded-xl shadow-sm border-l-4 cursor-pointer transition-all duration-300
        hover:shadow-md mb-3 group relative overflow-hidden
        ${getBorderColor(store.primaryCategory)}
        ${isSelected ? 'ring-2 ring-gray-900 bg-gray-50 transform scale-[1.01]' : 'border-gray-100'}
      `}
    >
      {/* Header */}
      <div className="flex justify-between items-start mb-2">
        <div className="flex-1 pr-2">
          <h3 className="font-bold text-gray-900 text-lg leading-tight group-hover:text-blue-900 transition-colors">
            {store.name}
          </h3>
          <div className="flex items-center text-gray-500 text-xs mt-1">
            <MapPin size={12} className="mr-1 flex-shrink-0" />
            <span className="truncate max-w-[180px]">{store.address}</span>
          </div>
        </div>
        <div className="flex flex-col items-end gap-2">
            <span className={`text-[10px] font-bold px-2 py-1 rounded-full whitespace-nowrap ${getBadgeColor(store.primaryCategory)}`}>
            {store.primaryCategory === LotteryType.LOTTO ? '로또' : '연금'}
            </span>
            <ChevronDown 
                size={16} 
                className={`text-gray-400 transition-transform duration-300 ${isSelected ? 'rotate-180' : ''}`} 
            />
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-3 gap-2 mt-3">
        <div className="bg-red-50 rounded-lg p-2 flex flex-col items-center justify-center border border-red-100">
          <span className="text-[10px] text-red-600 font-bold mb-0.5 flex items-center">
            <Trophy size={10} className="mr-1" /> 로또 1등
          </span>
          <span className="text-lg font-black text-gray-900">{store.wins.lotto1}</span>
        </div>
        <div className="bg-orange-50 rounded-lg p-2 flex flex-col items-center justify-center border border-orange-100">
          <span className="text-[10px] text-orange-600 font-bold mb-0.5 flex items-center">
            <Award size={10} className="mr-1" /> 로또 2등
          </span>
          <span className="text-lg font-black text-gray-900">{store.wins.lotto2}</span>
        </div>
        <div className="bg-blue-50 rounded-lg p-2 flex flex-col items-center justify-center border border-blue-100">
          <span className="text-[10px] text-blue-600 font-bold mb-0.5 flex items-center">
            <Star size={10} className="mr-1" /> 연금복권
          </span>
          <span className="text-lg font-black text-gray-900">{store.wins.pension}</span>
        </div>
      </div>

      {/* Evidence History (Show when selected) */}
      <div className={`grid transition-all duration-300 ease-in-out ${isSelected ? 'grid-rows-[1fr] mt-4 pt-3 border-t border-gray-200' : 'grid-rows-[0fr] mt-0 pt-0 border-t-0 border-transparent'}`}>
        <div className="overflow-hidden">
          <div className="flex items-center mb-2">
            <CheckCircle2 size={12} className="text-green-600 mr-1.5" />
            <h4 className="text-xs font-bold text-gray-700">최근 당첨 인증</h4>
          </div>
          <div className="bg-white rounded-md border border-gray-200 overflow-hidden">
            <ul className="text-xs divide-y divide-gray-100 max-h-[150px] overflow-y-auto custom-scrollbar">
              {store.history.map((record) => (
                <li key={record.id} className="flex justify-between items-center px-3 py-2 hover:bg-gray-50">
                  <div className="flex items-center">
                    <span className={`
                      inline-block w-1.5 h-1.5 rounded-full mr-2
                      ${record.type === LotteryType.LOTTO ? 'bg-red-500' : 'bg-blue-500'}
                    `}></span>
                    <span className="font-medium text-gray-800 w-16">{record.round}회</span>
                    {record.type === LotteryType.LOTTO ? (
                      <span className={`ml-1 px-1.5 py-0.5 rounded text-[10px] font-medium ${
                        record.rank === 1 ? 'bg-red-100 text-red-700' : 'bg-orange-100 text-orange-700'
                      }`}>
                        {record.rank}등
                        {record.rank === 1 && record.method && (
                          <span className="ml-1 text-gray-500 font-normal">({record.method})</span>
                        )}
                      </span>
                    ) : (
                      <span className="ml-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-100 text-blue-700">
                        1등
                      </span>
                    )}
                  </div>
                  <span className="text-gray-400 text-[10px]">{record.date}</span>
                </li>
              ))}
              {store.history.length === 0 && (
                <li className="px-3 py-2 text-center text-gray-400 italic">등록된 상세 이력이 없습니다.</li>
              )}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StoreCard;