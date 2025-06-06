import React, { useEffect, useState } from "react";
import { WeatherHeader } from "../components/weather-header";
import { WeatherNewsContainer } from "./weather-news-container";
import { HourlyForecast } from "../components/hourly-forecast";
import { ChatAssistant } from "../components/chat-assistant";
import { useWeather } from "../lib/weather-context";
import { getTemperatureGradient } from "../lib/utils";
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
  } = useWeather();
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

        setCurrentTemp(currentTempNumber);
        setWeatherLocation("현재 위치"); // 위치 이름은 필요시 API 응답이나 다른 방법으로 설정

        setWeatherData({
          location: "현재 위치", // 이 부분도 API 응답이나 다른 소스에서 가져올 수 있음
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
        setLocation(newLocation);
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
  }, [setCurrentTemp, setWeatherLocation]);

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
            <WeatherHeader
              currentTemp={weatherData.currentTemp}
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

        {location && !isLoadingWeather && (
          <WeatherNewsContainer
            latitude={location.latitude}
            longitude={location.longitude}
          />
        )}

        <div className="h-24" />
      </div>
    </div>
  );
}
