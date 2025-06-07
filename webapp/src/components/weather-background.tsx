import React from 'react';

interface WeatherBackgroundProps {
  sky: number; // 1: 맑음, 2: 구름조금, 3: 구름많음, 4: 흐림
  pty: number; // 0: 없음, 1: 비, 2: 비/눈, 3: 눈, 4: 소나기
  temp: number;
}

export function WeatherBackground({ sky, pty, temp }: WeatherBackgroundProps) {
  // 날씨 상태에 따른 배경 색상
  const getBackgroundGradient = () => {
    if (pty > 0) {
      // 비나 눈이 올 때
      return "from-gray-400/20 via-slate-200/30 to-blue-100/40";
    }
    
    if (sky >= 3) {
      // 구름많음, 흐림
      return "from-gray-300/20 via-slate-100/30 to-white";
    }
    
    // 맑음이나 구름조금일 때는 기온에 따른 색상
    if (temp >= 30) return "from-red-50/70 via-orange-100/70 to-yellow-50/50";
    if (temp >= 25) return "from-orange-50/70 via-yellow-100/70 to-white";
    if (temp >= 20) return "from-yellow-50/70 via-green-100/70 to-white";
    if (temp >= 15) return "from-green-50/70 via-blue-100/70 to-white";
    if (temp >= 10) return "from-blue-50/70 via-indigo-100/70 to-white";
    if (temp >= 5) return "from-indigo-50/70 via-purple-100/70 to-white";
    return "from-purple-50/70 via-blue-100/70 to-white";
  };

  // 태양 표시 여부
  const showSun = sky <= 2 && pty === 0;
  
  // 구름 표시 여부 및 개수
  const getCloudCount = () => {
    if (pty > 0) return 4; // 비올 때는 구름 많이
    if (sky === 4) return 4; // 흐림
    if (sky === 3) return 3; // 구름많음
    if (sky === 2) return 2; // 구름조금
    return 0; // 맑음
  };

  // 비/눈 표시 여부
  const showPrecipitation = pty > 0;
  const isSnow = pty === 3 || pty === 2;

  return (
    <div className={`absolute inset-0 bg-gradient-to-br ${getBackgroundGradient()} overflow-hidden`}>
      
      {/* 태양 */}
      {showSun && (
        <div className="absolute top-12 right-8 w-20 h-20">
          <div className="relative w-full h-full">
            {/* 태양 몸체 */}
            <div className="w-16 h-16 bg-yellow-300 rounded-full shadow-lg animate-pulse">
              <div className="w-full h-full bg-gradient-to-br from-yellow-200 to-orange-300 rounded-full"></div>
            </div>
            
            {/* 태양 광선들 */}
            {[...Array(8)].map((_, i) => (
              <div
                key={i}
                className="absolute w-1 h-6 bg-yellow-300 opacity-60 animate-pulse"
                style={{
                  top: '50%',
                  left: '50%',
                  transformOrigin: '50% 32px',
                  transform: `translate(-50%, -50%) rotate(${i * 45}deg)`,
                  animationDelay: `${i * 0.2}s`
                }}
              />
            ))}
          </div>
        </div>
      )}

      {/* 구름들 */}
      {[...Array(getCloudCount())].map((_, i) => (
        <div
          key={i}
          className="absolute opacity-80 animate-bounce"
          style={{
            top: `${15 + i * 12}%`,
            left: `${10 + i * 20}%`,
            animationDelay: `${i * 1.5}s`,
            animationDuration: '3s'
          }}
        >
          <CloudComponent size={i === 0 ? 'large' : i === 1 ? 'medium' : 'small'} />
        </div>
      ))}

      {/* 비/눈 */}
      {showPrecipitation && (
        <div className="absolute inset-0">
          {[...Array(isSnow ? 20 : 30)].map((_, i) => (
            <div
              key={i}
              className={`absolute ${isSnow ? 'w-1 h-1 bg-white rounded-full animate-ping' : 'w-0.5 h-8 bg-blue-400 opacity-60 animate-pulse'}`}
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 2}s`,
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// 구름 컴포넌트
function CloudComponent({ size }: { size: 'small' | 'medium' | 'large' }) {
  const sizeClasses = {
    small: 'w-12 h-8',
    medium: 'w-16 h-10',
    large: 'w-20 h-12'
  };

  return (
    <div className={`relative ${sizeClasses[size]}`}>
      {/* 구름 모양 만들기 */}
      <div className="absolute inset-0 bg-white/70 rounded-full"></div>
      <div className="absolute left-2 top-1 w-6 h-6 bg-white/80 rounded-full"></div>
      <div className="absolute right-2 top-1 w-6 h-6 bg-white/80 rounded-full"></div>
      <div className="absolute left-1/2 transform -translate-x-1/2 -top-1 w-8 h-8 bg-white/90 rounded-full"></div>
    </div>
  );
}

export default WeatherBackground;