import React, { useEffect, useState } from "react";
import { WeatherHeader } from "../components/weather-header";
import { WeatherNewsContainer } from "./weather-news-container";
import { HourlyForecast } from "../components/hourly-forecast";
import { ChatAssistant } from "../components/chat-assistant";
import { WeatherIndices } from "../components/weather-indices";
import { useWeather } from "../lib/weather-context";
import {
  getUltraShortTermWeather,
  getShortTermWeather,
  type UltraShortTermWeatherResponse,
  type ShortTermWeatherResponse,
  type WeatherApiItem,
} from "../lib/weather-api";
import { urlBase64ToUint8Array } from "@/lib/subscribe";

// 시간대별 날씨 데이터 타입
interface TimeSlot {
  time: string;
  temp: number;
  sky: number; // 하늘상태
  pty: number; // 강수형태
  windU: number; // 동서바람성분 (UUU)
  windV: number; // 남북바람성분 (VVV)
  humidity: number; // 습도 (REH)
}

// 시간 포맷팅 함수 (HHMM -> H PM/AM)
const formatTime = (timeString: string): string => {
  const hour = parseInt(timeString.substring(0, 2));
  const period = hour >= 12 ? "PM" : "AM";
  const displayHour = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour;
  return `${displayHour} ${period}`;
};

// 날짜와 시간을 조합하여 정렬 키 생성
const getDateTimeKey = (fcstDate: string, fcstTime: string): string => {
  return `${fcstDate}_${fcstTime}`;
};

// API 데이터를 TimeSlot 배열로 변환 (초단기 + 단기 예보 조합)
const processWeatherData = (
  ultraShortTermData: WeatherApiItem[],
  shortTermData: WeatherApiItem[]
): TimeSlot[] => {
  // 모든 데이터를 조합
  const allData = [...ultraShortTermData, ...shortTermData];

  // 시간별로 그룹화 (날짜_시간을 키로 사용)
  const timeGroups: { [key: string]: { [category: string]: string } } = {};

  allData.forEach((item) => {
    const timeKey = getDateTimeKey(item.fcstDate, item.fcstTime);
    if (!timeGroups[timeKey]) {
      timeGroups[timeKey] = {};
    }
    // 같은 시간대에 초단기와 단기 데이터가 모두 있는 경우, 초단기 데이터 우선
    if (!timeGroups[timeKey][item.category]) {
      timeGroups[timeKey][item.category] = item.fcstValue;
    }
  });

  // TimeSlot 배열 생성
  const timeSlots: TimeSlot[] = Object.entries(timeGroups)
    .map(([dateTimeKey, data]) => {
      const [, fcstTime] = dateTimeKey.split("_");
      return {
        time: formatTime(fcstTime),
        temp: parseInt(data.TMP || data.T1H || "0"), // 단기예보는 TMP, 초단기는 T1H
        sky: parseInt(data.SKY || "1"), // 하늘상태 (기본값: 맑음)
        pty: parseInt(data.PTY || "0"), // 강수형태 (기본값: 없음)
        windU: parseInt(data.UUU || "0"), // 동서바람성분
        windV: parseInt(data.VVV || "0"), // 남북바람성분
        humidity: parseInt(data.REH || "50"), // 습도 (기본값: 50%)
      };
    })
    .sort((a, b) => {
      // 시간순 정렬을 위해 원본 날짜_시간 문자열 사용
      const timeKeyA =
        Object.keys(timeGroups).find((key) => {
          const [, fcstTime] = key.split("_");
          return formatTime(fcstTime) === a.time;
        }) || "";
      const timeKeyB =
        Object.keys(timeGroups).find((key) => {
          const [, fcstTime] = key.split("_");
          return formatTime(fcstTime) === b.time;
        }) || "";
      return timeKeyA.localeCompare(timeKeyB);
    });

  // 최대 12시간 데이터 반환 (초단기 6시간 + 단기 6시간)
  return timeSlots.slice(0, 12);
};

export function WeatherDashboard() {
  const {
    userId,
    setCurrentTemp,
    setLocation: setWeatherLocation,
    coordinates,
    setCoordinates,
  } = useWeather();
  const [locationError, setLocationError] = useState<string | null>(null);
  const [weatherData, setWeatherData] = useState<{
    location: string;
    currentTemp: string;
    timeSlots: TimeSlot[];
  } | null>(null);
  const [isLoadingWeather, setIsLoadingWeather] = useState(false);
  const [weatherError, setWeatherError] = useState<string | null>(null);
  const [showStickyChat, setShowStickyChat] = useState(false);
  
  // 발표용 날씨 오버라이드 상태
  const [weatherOverride, setWeatherOverride] = useState<{
    enabled: boolean;
    sky: number;
    pty: number;
    temp: number;
  }>({ enabled: false, sky: 1, pty: 0, temp: 22 });
  
  const [showControls, setShowControls] = useState(false);

  // 스크롤 감지 함수
  useEffect(() => {
    const handleScroll = () => {
      // WeatherHeader의 높이를 기준으로 스크롤 위치 판단
      // 대략 200px 이상 스크롤되면 sticky chat 표시
      const scrollPosition = window.scrollY;
      setShowStickyChat(scrollPosition > 200);
    };

    window.addEventListener("scroll", handleScroll);
    return () => {
      window.removeEventListener("scroll", handleScroll);
    };
  }, []);

  // 위치 정보 가져오기 및 날씨 데이터 가져오기 통합 Effect
  useEffect(() => {
    const fetchAndSetWeatherData = async (lat: number, lon: number) => {
      setIsLoadingWeather(true);
      setWeatherError(null);
      try {
        // API 호출 (새로운 함수 사용)
        const ultraShortTermData: UltraShortTermWeatherResponse =
          await getUltraShortTermWeather(lat, lon);
        const shortTermData: ShortTermWeatherResponse =
          await getShortTermWeather(lat, lon);

        // API 응답에서 requestCode 확인 (실제 API 스펙에 따라 다를 수 있음)
        // 예를 들어, 성공 코드가 '200'이 아닌 다른 값일 수 있거나,
        // 또는 HTTP 상태 코드로만 성공 여부를 판단할 수도 있습니다.
        // 여기서는 기존 로직과 유사하게 requestCode를 확인합니다.
        if (
          ultraShortTermData.requestCode !== "200" ||
          shortTermData.requestCode !== "200"
        ) {
          // 실제 API가 오류 메시지를 어떻게 반환하는지에 따라 에러 처리를 조정해야 합니다.
          // 예를 들어 data.message 또는 다른 필드에 오류 내용이 있을 수 있습니다.
          throw new Error(
            `API error with code: ${ultraShortTermData.requestCode} or ${shortTermData.requestCode}`
          );
        }

        const timeSlots = processWeatherData(
          ultraShortTermData.items,
          shortTermData.items
        );
        const currentTemp =
          timeSlots.length > 0 ? `${timeSlots[0].temp}°C` : "N/A";
        const currentTempNumber = timeSlots.length > 0 ? timeSlots[0].temp : 20;

        // 단기 데이터에서 location 정보 추출
        const locationName = ultraShortTermData.location || "현재 위치";

        setCurrentTemp(currentTempNumber);
        setWeatherLocation(locationName);

        setWeatherData({
          location: locationName,
          currentTemp,
          timeSlots,
        });
      } catch (error) {
        console.error("날씨 데이터 가져오기 실패:", error);
        setWeatherError(
          error instanceof Error
            ? error.message
            : "날씨 데이터를 가져올 수 없습니다."
        );
        setWeatherData(null);
      } finally {
        setIsLoadingWeather(false);
      }
    };

    if (!navigator.geolocation) {
      setLocationError("이 브라우저는 위치 서비스를 지원하지 않습니다.");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const newLocation = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        };
        setCoordinates(newLocation);
        fetchAndSetWeatherData(newLocation.latitude, newLocation.longitude);
      },
      (error) => {
        let errorMessage = "위치를 가져올 수 없습니다.";
        switch (error.code) {
          case error.PERMISSION_DENIED:
            errorMessage = "위치 접근이 거부되었습니다.";
            break;
          case error.POSITION_UNAVAILABLE:
            errorMessage = "위치 정보를 사용할 수 없습니다.";
            break;
          case error.TIMEOUT:
            errorMessage = "위치 요청 시간이 초과되었습니다.";
            break;
        }
        setLocationError(errorMessage);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 300000, // 5분간 캐시된 위치 사용
      }
    );
  }, [setCurrentTemp, setWeatherLocation, setCoordinates]);

  // 현재 날씨 상태 (첫 번째 타임슬롯에서 가져오기 또는 오버라이드)
  const currentWeather = weatherOverride.enabled 
    ? weatherOverride 
    : (weatherData?.timeSlots[0] || {
        temp: 25, // 테스트용 기본값
        sky: 4,   // 4: 흐림 (테스트)
        pty: 0    // 0: 비/눈 없음
      });

  // 디버그용 로그
  console.log('날씨 데이터:', weatherData);
  console.log('현재 날씨:', currentWeather);

  // 날씨에 따른 배경 색상 계산
  const getWeatherBackground = () => {
    const weather = currentWeather;
    
    console.log('배경 계산 중:', weather); // 디버그
    
    if (weather.pty > 0) {
      // 비나 눈이 올 때 - 진한 회색
      return "from-gray-600/60 via-slate-400/70 to-blue-300/80";
    }
    
    if (weather.sky >= 3) {
      // 구름많음, 흐림 - 회색조
      return "from-gray-400/60 via-slate-300/70 to-gray-200/80";
    }
    
    // 맑음이나 구름조금일 때는 기온에 따른 색상
    if (weather.temp >= 30) return "from-red-200/80 via-orange-300/80 to-yellow-200/80";
    if (weather.temp >= 25) return "from-orange-200/80 via-yellow-300/80 to-green-200/80";
    if (weather.temp >= 20) return "from-yellow-200/80 via-green-300/80 to-blue-200/80";
    if (weather.temp >= 15) return "from-green-200/80 via-blue-300/80 to-indigo-200/80";
    if (weather.temp >= 10) return "from-blue-200/80 via-indigo-300/80 to-purple-200/80";
    if (weather.temp >= 5) return "from-indigo-200/80 via-purple-300/80 to-blue-200/80";
    return "from-purple-200/80 via-blue-300/80 to-indigo-200/80";
  };

  return (
    <div className={`max-w-lg w-full mx-auto min-h-screen flex flex-col relative pb-16 bg-gradient-to-br ${getWeatherBackground()} transition-all duration-1000 ease-in-out`}>
      {/* 발표용 컴트롤 토글 버튼 */}
      <button
        onClick={() => setShowControls(!showControls)}
        className="fixed top-4 right-4 z-50 bg-black/20 hover:bg-black/30 text-white p-2 rounded-full transition-all"
        title="발표용 컴트롤"
      >
        Test
      </button>

      {/* 발표용 컴트롤 패널 */}
      {showControls && (
        <div className="fixed top-16 right-4 z-50 bg-white/95 backdrop-blur-sm p-4 rounded-lg shadow-lg border max-w-xs">
          
          <div className="space-y-3">
            {/* 오버라이드 대시니보드 */}
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={weatherOverride.enabled}
                onChange={(e) => setWeatherOverride(prev => ({ ...prev, enabled: e.target.checked }))}
                className="rounded"
              />
              <span className="text-sm font-medium">데모 모드</span>
            </label>

            {weatherOverride.enabled && (
              <>
                {/* 기온 */}
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    기온: {weatherOverride.temp}°C
                  </label>
                  <input
                    type="range"
                    min="-10"
                    max="40"
                    value={weatherOverride.temp}
                    onChange={(e) => setWeatherOverride(prev => ({ ...prev, temp: parseInt(e.target.value) }))}
                    className="w-full h-1 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  />
                </div>

                {/* 하늘상태 */}
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    하늘: {['', '맑음', '구름조금', '구름많음', '흐림'][weatherOverride.sky]}
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="4"
                    value={weatherOverride.sky}
                    onChange={(e) => setWeatherOverride(prev => ({ ...prev, sky: parseInt(e.target.value) }))}
                    className="w-full h-1 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  />
                </div>

                {/* 강수형태 */}
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    강수: {['없음', '비', '비/눈', '눈', '소나기'][weatherOverride.pty]}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="4"
                    value={weatherOverride.pty}
                    onChange={(e) => setWeatherOverride(prev => ({ ...prev, pty: parseInt(e.target.value) }))}
                    className="w-full h-1 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  />
                </div>

                {/* 프리셋 버튼
                <div className="pt-2 border-t">
                  <div className="text-xs font-medium text-gray-700 mb-2">빠른 설정:</div>
                  <div className="grid grid-cols-2 gap-1">
                    <button
                      onClick={() => setWeatherOverride(prev => ({ ...prev, sky: 1, pty: 0, temp: 30 }))}
                      className="text-xs px-2 py-1 bg-yellow-100 hover:bg-yellow-200 rounded transition-colors"
                    >
                      ☀️ 맑음
                    </button>
                    <button
                      onClick={() => setWeatherOverride(prev => ({ ...prev, sky: 4, pty: 0, temp: 18 }))}
                      className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded transition-colors"
                    >
                      ☁️ 흐림
                    </button>
                    <button
                      onClick={() => setWeatherOverride(prev => ({ ...prev, sky: 4, pty: 1, temp: 15 }))}
                      className="text-xs px-2 py-1 bg-blue-100 hover:bg-blue-200 rounded transition-colors"
                    >
                      🌧️ 비
                    </button>
                    <button
                      onClick={() => setWeatherOverride(prev => ({ ...prev, sky: 4, pty: 3, temp: -2 }))}
                      className="text-xs px-2 py-1 bg-indigo-100 hover:bg-indigo-200 rounded transition-colors"
                    >
                      ❄️ 눈
                    </button>
                  </div>
                </div> */}
              </>
            )}
          </div>
        </div>
      )}
      {/* 날씨 상태 정보
      <div className="absolute top-4 left-4 z-50 bg-black/30 text-white p-2 rounded-lg text-xs font-mono">
        T:{currentWeather.temp}°C | SKY:{currentWeather.sky} | PTY:{currentWeather.pty}
        <div className="text-xs opacity-75">
          {currentWeather.sky >= 3 ? '흐림/구름많음' : currentWeather.sky === 2 ? '구름조금' : '맑음'}
        </div>
      </div> */}

      {/* 날씨 애니메이션 요소들 */}
      {currentWeather.sky <= 2 && currentWeather.pty === 0 && (
        // 맑은 날씨일 때 태양
        <div className="absolute top-12 right-8 w-16 h-16">
          <div className="w-full h-full bg-yellow-300 rounded-full shadow-lg animate-pulse opacity-90">
            <div className="w-full h-full bg-gradient-to-br from-yellow-200 to-orange-300 rounded-full"></div>
          </div>
          {/* 태양 광선 */}
          {[...Array(8)].map((_, i) => (
            <div
              key={i}
              className="absolute w-0.5 h-4 bg-yellow-300 opacity-60 animate-pulse"
              style={{
                top: '50%',
                left: '50%',
                transformOrigin: '50% 24px',
                transform: `translate(-50%, -50%) rotate(${i * 45}deg)`,
                animationDelay: `${i * 0.3}s`
              }}
            />
          ))}
        </div>
      )}
      
      {currentWeather.sky >= 3 && (
        // 구름많음/흐림일 때 구름
        <>
          <div className="absolute top-16 left-8 w-16 h-10 bg-white/70 rounded-full animate-bounce shadow-md" style={{animationDelay: '0s', animationDuration: '4s'}}>
            <div className="absolute inset-0 bg-gray-100/50 rounded-full"></div>
          </div>
          <div className="absolute top-20 right-12 w-12 h-8 bg-white/60 rounded-full animate-bounce shadow-md" style={{animationDelay: '1s', animationDuration: '5s'}}>
            <div className="absolute inset-0 bg-gray-100/40 rounded-full"></div>
          </div>
          <div className="absolute top-32 left-16 w-14 h-9 bg-white/80 rounded-full animate-bounce shadow-md" style={{animationDelay: '2s', animationDuration: '6s'}}>
            <div className="absolute inset-0 bg-gray-100/60 rounded-full"></div>
          </div>
          <div className="absolute top-24 right-6 w-10 h-7 bg-white/50 rounded-full animate-bounce shadow-md" style={{animationDelay: '1.5s', animationDuration: '4.5s'}}>
            <div className="absolute inset-0 bg-gray-100/30 rounded-full"></div>
          </div>
        </>
      )}
      
      {currentWeather.pty > 0 && (
        // 비/눈이 올 때 효과
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          {[...Array(30)].map((_, i) => (
            <div
              key={i}
              className={`absolute ${currentWeather.pty === 3 ? 'w-1 h-1 bg-white rounded-full' : 'w-0.5 h-6 bg-blue-400 opacity-70'} animate-pulse`}
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 80 + 10}%`,
                animationDelay: `${Math.random() * 2}s`,
                animationDuration: `${1 + Math.random() * 2}s`
              }}
            />
          ))}
        </div>
      )}
      {/* Sticky Chat Assistant */}
      {showStickyChat && (
        <div className="fixed top-0 left-0 right-0 z-50 p-4 bg-white/80 backdrop-blur-md border-b border-gray-200/50">
          <div className="w-full">
            <ChatAssistant isSticky={true} />
          </div>
        </div>
      )}

      <div className={`relative z-10 ${showStickyChat ? "mt-20" : ""}`}>
        {weatherData && (
          <>
            <WeatherHeader
              currentTemp={weatherData.currentTemp}
              location={weatherData.location}
              onNotificationClick={async () => {
                const registration = await navigator.serviceWorker.ready;
                try {
                  const sub = await registration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: urlBase64ToUint8Array(
                      process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY!
                    ),
                  });
                  const subscription = sub.toJSON();
                  const res = await fetch(
                    `http://localhost:8000/notifications`,
                    {
                      method: "POST",
                      body: JSON.stringify({
                        user_id: userId,
                        endpoint: subscription.endpoint,
                        expirationTime: subscription.expirationTime || 0,
                        p256dh: subscription.keys?.p256dh || "",
                        auth: subscription.keys?.auth || "",
                      }),
                      headers: {
                        "Content-Type": "application/json",
                      },
                    }
                  );
                  if (!res.ok) {
                    throw new Error();
                  }
                } catch (e) {
                  console.error(e);
                  alert("Failed to subscribe to push notifications");
                  registration.pushManager.getSubscription().then((sub) => {
                    if (sub) {
                      sub.unsubscribe();
                    }
                  });
                }
              }}
            />
            <HourlyForecast timeSlots={weatherData.timeSlots} />
            <WeatherIndices slot={weatherData.timeSlots[0]} />
          </>
        )}

        {locationError && (
          <div className="p-6">
            <div className="bg-red-100/50 backdrop-blur-sm border border-red-200/50 rounded-lg p-4 text-center">
              <div className="text-red-700 font-medium">
                위치 에러: {locationError}
              </div>
            </div>
          </div>
        )}

        {weatherError && (
          <div className="p-6">
            <div className="bg-red-100/50 backdrop-blur-sm border border-red-200/50 rounded-lg p-4 text-center">
              <div className="text-red-700 font-medium mb-2">
                날씨 데이터를 불러올 수 없습니다
              </div>
            </div>
          </div>
        )}

        <div className="h-8" />

        {coordinates && !isLoadingWeather && (
          <WeatherNewsContainer
            latitude={coordinates.latitude}
            longitude={coordinates.longitude}
          />
        )}

        <div className="h-24" />
      </div>
    </div>
  );
}
