"use client";

import { useEffect, useState } from "react";
import { WeatherNews } from "../components/weather-news";
import { getWeatherNews, type WeatherNewsItem } from "../lib/weather-api";

interface WeatherNewsContainerProps {
  latitude: number;
  longitude: number;
}

export function WeatherNewsContainer({
  latitude,
  longitude,
}: WeatherNewsContainerProps) {
  // Use WeatherNewsItem as the state type
  const [newsArticles, setNewsArticles] = useState<WeatherNewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadWeatherNews = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await getWeatherNews(latitude, longitude);
        setNewsArticles(response);
      } catch (err) {
        const errorMessage =
          err instanceof Error
            ? err.message
            : "뉴스를 불러오는데 실패했습니다.";
        setError(errorMessage);
        console.error("날씨 뉴스 가져오기 에러:", err);
        setNewsArticles([]); // Clear articles on error
      } finally {
        setLoading(false);
      }
    };

    loadWeatherNews();
  }, [latitude, longitude]);

  if (loading) {
    return (
      <div className="p-6">
        <div className="bg-white/30 backdrop-blur-sm rounded-lg p-4 text-center">
          <div className="text-gray-700 font-medium">날씨 뉴스 로딩중...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-100/50 backdrop-blur-sm border border-red-200/50 rounded-lg p-4 text-center">
          <div className="text-red-700 font-medium">에러: {error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="px-6 space-y-4">
      <h2 className="text-xl font-bold text-gray-800 mb-4 drop-shadow-sm">
        현재 위치 날씨 뉴스
      </h2>
      {newsArticles.length === 0 ? (
        <div className="bg-white/30 backdrop-blur-sm rounded-lg p-4 text-center">
          <div className="text-gray-700 font-medium">뉴스 기사가 없습니다.</div>
        </div>
      ) : (
        newsArticles.map((article, idx) => (
          // Adapt props for WeatherNews component
          // It expects newsTitle, summary, articleUrl
          <WeatherNews
            key={idx} // Use unique id from news item
            newsTitle={article.title}
            summary={article.summary || ""} // Provide default for optional summary
            articleUrl={article.url} // Use url field
          />
        ))
      )}
    </div>
  );
}
