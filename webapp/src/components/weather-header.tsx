import React from "react";

type WeatherHeaderProps = {
  location: string;
  currentTemp: string;
  highTemp: string;
  lowTemp: string;
  weatherMessage: string;
};

export function WeatherHeader({
  location,
  currentTemp,
  highTemp,
  lowTemp,
  weatherMessage,
}: WeatherHeaderProps) {
  return (
    <div className="mb-4 pt-4">
      <div className="flex justify-between items-start">
        <div className="text-xl font-bold">{location}</div>
        <div className="text-xl">99</div>
      </div>

      <div className="flex justify-between items-center">
        <div>
          <div className="text-6xl font-bold">{currentTemp}</div>
          <div className="text-xl">
            ( <span className="text-red-500">{highTemp}</span> /{" "}
            <span className="text-blue-500">{lowTemp}</span> )
          </div>
        </div>
        <div className="relative">
          <div className="relative">
            <svg
              width="120"
              height="120"
              viewBox="0 0 120 120"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M40 70C40 50 60 45 75 60C90 75 100 50 100 50"
                stroke="#3B82F6"
                strokeWidth="2"
              />
              <circle
                cx="60"
                cy="60"
                r="25"
                fill="none"
                stroke="#374151"
                strokeWidth="2"
              />
              <path
                d="M50 55C50 55 55 60 60 60C65 60 70 55 70 55"
                stroke="#374151"
                strokeWidth="2"
              />
              <circle cx="50" cy="50" r="3" fill="#374151" />
              <circle cx="70" cy="50" r="3" fill="#374151" />
            </svg>
            <div className="absolute top-0 right-0 bg-white rounded-xl p-2 border border-gray-300">
              &ldquo;{weatherMessage}&rdquo;
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
