import React from "react";
import { ExternalLink } from "lucide-react";

type WeatherNewsProps = {
  newsTitle: string;
  summary: string;
  articleUrl?: string;
};

export function WeatherNews({
  newsTitle,
  summary,
  articleUrl,
}: WeatherNewsProps) {
  return (
    <div className="border border-white/30 rounded-lg p-4 flex-grow mb-4 shadow-sm hover:shadow-md transition-all duration-200">
      <h3 className="font-semibold text-gray-800 mb-2">{newsTitle}</h3>
      <p className="text-sm text-gray-700 mb-3 line-clamp-2">{summary}</p>

      {articleUrl && (
        <div className="text-right">
          <a
            href={articleUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center text-xs text-blue-700 hover:text-blue-900 hover:underline font-medium"
          >
            <span className="mr-1">Read more</span>
            <ExternalLink size={12} />
          </a>
        </div>
      )}
    </div>
  );
}
