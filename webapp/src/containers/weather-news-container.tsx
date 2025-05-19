"use client";

import { useEffect, useState } from "react";
import { WeatherNews } from "../components/weather-news";

type NewsArticle = {
  articleTitle: string;
  articleSummary: string;
  articleUrl: string;
};

export function WeatherNewsContainer({
  location = "춘천",
}: {
  location?: string;
}) {
  const [newsArticles, setNewsArticles] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchNews = async () => {
      try {
        setLoading(true);
        const response = await fetch(
          `http://localhost:8000/weather/news?location=${encodeURIComponent(
            location
          )}`
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
  }, [location]);

  if (loading) {
    return <div className="p-4">날씨 뉴스 로딩중...</div>;
  }

  if (error) {
    return <div className="p-4 text-red-500">에러: {error}</div>;
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold mb-4">{location} 날씨 뉴스</h2>
      {newsArticles.length === 0 ? (
        <div>뉴스 기사가 없습니다.</div>
      ) : (
        newsArticles.map((article, index) => (
          <a
            key={index}
            href={article.articleUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="block"
          >
            <WeatherNews
              newsTitle={article.articleTitle}
              summary={article.articleSummary}
            />
          </a>
        ))
      )}
    </div>
  );
}
