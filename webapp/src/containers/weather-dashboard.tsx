import React, { useEffect, useState } from "react";
import { WeatherHeader } from "../components/weather-header";
import { WeatherNewsContainer } from "./weather-news-container";
import { HourlyForecast } from "../components/hourly-forecast";
import { ChatAssistant } from "../components/chat-assistant";
import { useWeather } from "../lib/weather-context";

// API 응답 타입 정의
interface WeatherApiItem {
  fcstDate: string;
  fcstTime: string;
  category: string;
  fcstValue: string;
}

interface WeatherApiResponse {
  requestCode: string;
  items: WeatherApiItem[];
}

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

// 기온에 따른 배경 그라데이션 색상 (더 연하고 흰색에 가까운 색상)
const getTemperatureGradient = (temp: number): string => {
  if (temp >= 30) return "from-red-50 via-orange-25 to-white";
  if (temp >= 25) return "from-orange-50 via-yellow-25 to-white";
  if (temp >= 20) return "from-yellow-50 via-green-25 to-white";
  if (temp >= 15) return "from-green-50 via-blue-25 to-white";
  if (temp >= 10) return "from-blue-50 via-indigo-25 to-white";
  if (temp >= 5) return "from-indigo-50 via-purple-25 to-white";
  return "from-purple-50 via-blue-25 to-white";
};

// 시간 포맷팅 함수 (HHMM -> H PM/AM)
const formatTime = (timeString: string): string => {
  const hour = parseInt(timeString.substring(0, 2));
  const period = hour >= 12 ? "PM" : "AM";
  const displayHour = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour;
  return `${displayHour} ${period}`;
};

// API 데이터를 TimeSlot 배열로 변환
const processWeatherData = (apiData: WeatherApiItem[]): TimeSlot[] => {
  // 시간별로 그룹화
  const timeGroups: { [key: string]: { [category: string]: string } } = {};

  apiData.forEach((item) => {
    const timeKey = item.fcstTime;
    if (!timeGroups[timeKey]) {
      timeGroups[timeKey] = {};
    }
    timeGroups[timeKey][item.category] = item.fcstValue;
  });

  // TimeSlot 배열 생성
  const timeSlots: TimeSlot[] = Object.entries(timeGroups)
    .map(([time, data]) => ({
      time: formatTime(time),
      temp: parseInt(data.T1H || "0"), // 기온
      sky: parseInt(data.SKY || "1"), // 하늘상태 (기본값: 맑음)
      pty: parseInt(data.PTY || "0"), // 강수형태 (기본값: 없음)
      windU: parseInt(data.UUU || "0"), // 동서바람성분
      windV: parseInt(data.VVV || "0"), // 남북바람성분
      humidity: parseInt(data.REH || "50"), // 습도 (기본값: 50%)
    }))
    .sort((a, b) => {
      // 시간순 정렬을 위해 원본 시간 문자열 사용
      const timeA =
        Object.keys(timeGroups).find((key) => formatTime(key) === a.time) || "";
      const timeB =
        Object.keys(timeGroups).find((key) => formatTime(key) === b.time) || "";
      return timeA.localeCompare(timeB);
    });

  // 최대 6시간 데이터만 반환
  return timeSlots.slice(0, 6);
};

export function WeatherDashboard() {
  const { setCurrentTemp, setLocation: setWeatherLocation } = useWeather();
  const [location, setLocation] = useState<{
    latitude: number;
    longitude: number;
  } | null>(null);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [weatherData, setWeatherData] = useState<{
    location: string;
    currentTemp: string;
    timeSlots: TimeSlot[];
  } | null>(null);
  const [isLoadingWeather, setIsLoadingWeather] = useState(false);
  const [weatherError, setWeatherError] = useState<string | null>(null);
  const [showStickyChat, setShowStickyChat] = useState(false);

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

  // 날씨 데이터 가져오기 함수
  const fetchWeatherData = async (latitude: number, longitude: number) => {
    setIsLoadingWeather(true);
    setWeatherError(null);

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/weather/ultra_short_term?latitude=${latitude}&longitude=${longitude}`
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: WeatherApiResponse = await response.json();

      if (data.requestCode !== "200") {
        throw new Error(`API error! code: ${data.requestCode}`);
      }

      const timeSlots = processWeatherData(data.items);
      const currentTemp =
        timeSlots.length > 0 ? `${timeSlots[0].temp}°C` : "N/A";
      const currentTempNumber = timeSlots.length > 0 ? timeSlots[0].temp : 20;

      // Context에 온도 데이터 업데이트
      setCurrentTemp(currentTempNumber);
      setWeatherLocation("현재 위치");

      setWeatherData({
        location: "현재 위치",
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
      // 에러 발생 시에는 weatherData를 null로 설정
      setWeatherData(null);
    } finally {
      setIsLoadingWeather(false);
    }
  };

  // 위치 정보 가져오기
  useEffect(() => {
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
        setLocation(newLocation);

        // 위치를 얻으면 바로 날씨 데이터 가져오기
        fetchWeatherData(newLocation.latitude, newLocation.longitude);
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
  }, []);

  const backgroundGradient = weatherData
    ? getTemperatureGradient(weatherData.timeSlots[0]?.temp || 20)
    : "from-blue-50 via-indigo-25 to-white";

  return (
    <div
      className={`max-w-lg w-full mx-auto h-screen flex flex-col bg-gradient-to-br ${backgroundGradient} pb-16`}
    >
      {/* Sticky Chat Assistant */}
      {showStickyChat && (
        <div className="fixed top-0 left-0 right-0 z-50 p-4 bg-white/80 backdrop-blur-md border-b border-gray-200/50">
          <div className="w-full">
            <ChatAssistant isSticky={true} />
          </div>
        </div>
      )}

      <div className={showStickyChat ? "mt-20" : ""}>
        {weatherData && (
          <>
            <WeatherHeader currentTemp={weatherData.currentTemp} />
            <HourlyForecast timeSlots={weatherData.timeSlots} />
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
              <div className="text-red-600 text-sm mb-3">{weatherError}</div>
              <button
                onClick={() =>
                  location &&
                  fetchWeatherData(location.latitude, location.longitude)
                }
                className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                disabled={isLoadingWeather}
              >
                {isLoadingWeather ? "재시도 중..." : "다시 시도"}
              </button>
            </div>
          </div>
        )}

        {location && !isLoadingWeather && (
          <WeatherNewsContainer
            latitude={location.latitude}
            longitude={location.longitude}
          />
        )}
      </div>
    </div>
  );
}
