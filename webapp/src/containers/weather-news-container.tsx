"use client";

import { useEffect, useState } from "react";
import { WeatherNews } from "../components/weather-news";

type NewsArticle = {
  title: string;
  summary: string;
  link_url: string;
};

interface WeatherNewsContainerProps {
  latitude: number;
  longitude: number;
}

export function WeatherNewsContainer({
  latitude,
  longitude,
}: WeatherNewsContainerProps) {
  const [newsArticles, setNewsArticles] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchNews = async () => {
      try {
        setLoading(true);
        const response = await fetch(
          `http://localhost:8000/weather/news?latitude=${latitude}&longitude=${longitude}`
        );

        if (!response.ok) {
          throw new Error(`Failed to fetch news: ${response.status}`);
        }

        const data = await response.json();
        setNewsArticles(data as NewsArticle[]);
      } catch (err) {
        setError(err instanceof Error ? err.message : "에러 발생");
        console.error("날씨 뉴스 가져오기 에러:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchNews();
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
        newsArticles.map((article, index) => (
          <WeatherNews
            key={index}
            newsTitle={article.title}
            summary={article.summary}
            articleUrl={article.link_url}
          />
        ))
      )}
    </div>
  );
}
