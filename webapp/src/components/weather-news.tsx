import React from "react";

type WeatherNewsProps = {
  newsTitle: string;
  progress?: number;
};

export function WeatherNews({ newsTitle, progress = 50 }: WeatherNewsProps) {
  return (
    <div className="border border-gray-400 rounded p-4 flex-grow mb-4">
      <div>{newsTitle}</div>
      <div className="flex items-center mt-4">
        <div
          className="flex-grow h-2 bg-green-200 rounded"
          style={{ width: `${progress}%` }}
        ></div>
        <div className="text-3xl text-green-600 ml-2">N</div>
      </div>
    </div>
  );
}
