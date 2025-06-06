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
  requestCode: string;
  items: WeatherApiItem[];
  location: string;
}

// --- 날씨 데이터 (단기예보) ---
export interface ShortTermWeatherResponse {
  requestCode: string;
  items: WeatherApiItem[];
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

export async function getShortTermWeather(
  latitude: number,
  longitude: number
): Promise<ShortTermWeatherResponse> {
  const response = await fetch(
    `${API_BASE_URL}/weather/short_term?latitude=${latitude}&longitude=${longitude}`
  );

  if (!response.ok) {
    const errorData = (await response.json().catch(() => ({
      detail: "Unknown error while fetching short term weather data",
    }))) as ErrorResponse;
    throw new Error(
      errorData.detail || "Failed to fetch short term weather data"
    );
  }

  return response.json();
}

// --- 날씨 뉴스 ---
export interface WeatherNewsItem {
  title: string;
  link_url: string;
  source: string;
  publishTime: string; // 또는 Date 객체로 변환할 수 있는 문자열
  summary: string; // 요약 정보는 선택적일 수 있음
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
