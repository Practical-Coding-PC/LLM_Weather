// API 기본 설정
const API_BASE_URL =
  typeof window !== "undefined"
    ? process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
    : "http://localhost:8000";

interface ErrorResponse {
  detail: string;
}

// --- 날씨 데이터 (초단기예보) ---
export interface WeatherApiItem {
  fcstDate: string;
  fcstTime: string;
  category: string;
  fcstValue: string;
}

export interface UltraShortTermWeatherResponse {
  // FastAPI Pydantic 모델을 기반으로 실제 응답 구조를 정의해야 합니다.
  // 예시:
  // request_time: string;
  // base_date: string;
  // base_time: string;
  // nx: number;
  // ny: number;
  // items: WeatherApiItem[];
  // request_code: string; // 또는 resultCode 등으로 API 명세에 따라 다를 수 있음
  // message: string; // 성공/실패 메시지
  //
  // 현재 weather-dashboard.tsx에서 사용하는 구조와 FastAPI 응답 구조를
  // 일치시키거나, 여기서 변환 로직을 추가해야 합니다.
  // 여기서는 weather-dashboard.tsx의 WeatherApiResponse 와 유사하게 정의합니다.
  requestCode: string; // 실제 API 응답에 따라 이 필드명이 달라질 수 있습니다.
  items: WeatherApiItem[];
  // FastAPI 응답에 따라 다른 필드들이 있을 수 있습니다. (예: metadata, pagination 등)
}

export async function getUltraShortTermWeather(
  latitude: number,
  longitude: number
): Promise<UltraShortTermWeatherResponse> {
  const response = await fetch(
    `${API_BASE_URL}/weather/ultra_short_term?latitude=${latitude}&longitude=${longitude}`
  );

  if (!response.ok) {
    const errorData = (await response.json().catch(() => ({
      detail: "Unknown error while fetching weather data",
    }))) as ErrorResponse;
    throw new Error(
      errorData.detail || "Failed to fetch ultra short term weather data"
    );
  }

  return response.json();
}

// --- 날씨 뉴스 ---
export interface WeatherNewsItem {
  // 실제 API 응답 구조에 따라 정의해야 합니다.
  // 예시:
  // title: string;
  // link: string;
  // summary: string;
  // published_date: string;
  // source: string;
  //
  // 현재 webapp/src/components/weather-news-item.tsx 의 NewsItem props와 유사하게 정의합니다.
  title: string;
  url: string;
  source: string;
  publishTime: string; // 또는 Date 객체로 변환할 수 있는 문자열
  summary?: string; // 요약 정보는 선택적일 수 있음
}

export async function getWeatherNews(
  latitude: number,
  longitude: number
): Promise<WeatherNewsItem[]> {
  const response = await fetch(
    `${API_BASE_URL}/weather/news?latitude=${latitude}&longitude=${longitude}`
  );

  if (!response.ok) {
    const errorData = (await response.json().catch(() => ({
      detail: "Unknown error while fetching weather news",
    }))) as ErrorResponse;
    throw new Error(errorData.detail || "Failed to fetch weather news");
  }

  return response.json();
}
