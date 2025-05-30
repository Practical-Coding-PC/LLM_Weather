import React, { useEffect, useState } from "react";
import { WeatherHeader } from "../components/weather-header";
import { WeatherNewsContainer } from "./weather-news-container";
import { ChatAssistant } from "../components/chat-assistant";
import dynamic from "next/dynamic";

const HourlyForecast = dynamic(
  () =>
    import("../components/hourly-forecast").then((mod) => mod.HourlyForecast),
  {
    ssr: false,
  }
);

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

export function WeatherDashboard() {
  const [location, setLocation] = useState<{
    latitude: number;
    longitude: number;
  } | null>(null);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [isLoadingLocation, setIsLoadingLocation] = useState(true);

  useEffect(() => {
    if (!navigator.geolocation) {
      setLocationError("이 브라우저는 위치 서비스를 지원하지 않습니다.");
      setIsLoadingLocation(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        });
        setIsLoadingLocation(false);
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
        setIsLoadingLocation(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 300000, // 5분간 캐시된 위치 사용
      }
    );
  }, []);

  const weatherData = {
    location: "춘천",
    currentTemp: "25°C",
    timeSlots: [
      { time: "1 PM", temp: 12 },
      { time: "2 PM", temp: 13 },
      { time: "3 PM", temp: 24 },
      { time: "4 PM", temp: 23 },
      { time: "5 PM", temp: 25 },
      { time: "6 PM", temp: 35 },
    ],
  };

  const backgroundGradient = getTemperatureGradient(
    weatherData.timeSlots[0].temp
  );

  return (
    <div
      className={`max-w-md mx-auto h-screen flex flex-col bg-gradient-to-br ${backgroundGradient} overflow-auto`}
    >
      <WeatherHeader currentTemp={weatherData.currentTemp} />

      <HourlyForecast timeSlots={weatherData.timeSlots} />

      {isLoadingLocation ? (
        <div className="p-6">
          <div className="bg-white/30 backdrop-blur-sm rounded-lg p-4 text-center">
            <div className="text-gray-700 font-medium">
              위치 정보 가져오는 중...
            </div>
          </div>
        </div>
      ) : locationError ? (
        <div className="p-6">
          <div className="bg-red-100/50 backdrop-blur-sm border border-red-200/50 rounded-lg p-4 text-center">
            <div className="text-red-700 font-medium">
              위치 에러: {locationError}
            </div>
          </div>
        </div>
      ) : location ? (
        <WeatherNewsContainer
          latitude={location.latitude}
          longitude={location.longitude}
        />
      ) : null}

      <ChatAssistant onClick={() => console.log("Chat assistant clicked")} />
    </div>
  );
}
