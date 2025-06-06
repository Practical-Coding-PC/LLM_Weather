import { useEffect, useState } from "react";
import { ChatAssistant } from "./chat-assistant";

type WeatherHeaderProps = {
  currentTemp: string;
  location?: string;
  onNotificationClick: () => void;
};

export function WeatherHeader({
  currentTemp,
  location,
  onNotificationClick,
}: WeatherHeaderProps) {
  const [isSubscribed, setIsSubscribed] = useState(true);

  useEffect(() => {
    navigator.serviceWorker.ready.then((registration) => {
      registration.pushManager.getSubscription().then((subscription) => {
        setIsSubscribed(!!subscription);
      });
    });
  }, []);

  return (
    <div className="px-6 py-8 flex justify-between items-start">
      <div className="flex justify-between items-start mb-6">
        <div>
          <div className="flex items-center gap-1 mb-4">
            <h2 className="text-gray-700 text-lg">기온 </h2>
            <span>
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                className="text-gray-500 mb-1"
              >
                <path
                  d="M12 2C10.34 2 9 3.34 9 5V14.5C7.79 15.57 7 17.18 7 19C7 21.76 9.24 24 12 24S17 21.76 17 19C17 17.18 16.21 15.57 15 14.5V5C15 3.34 13.66 2 12 2ZM12 22C10.34 22 9 20.66 9 19C9 17.34 10.34 16 12 16S15 17.34 15 19C15 20.66 13.66 22 12 22Z"
                  fill="currentColor"
                />
              </svg>
            </span>
          </div>
          <span className="text-6xl font-semibold text-gray-800 drop-shadow-sm">
            {currentTemp}
          </span>
          {location && (
            <div className="mt-2 flex items-center gap-1">
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                className="text-gray-500"
              >
                <path
                  d="M12 2C8.13 2 5 5.13 5 9C5 14.25 12 22 12 22S19 14.25 19 9C19 5.13 15.87 2 12 2ZM12 11.5C10.62 11.5 9.5 10.38 9.5 9S10.62 6.5 12 6.5S14.5 7.62 14.5 9S13.38 11.5 12 11.5Z"
                  fill="currentColor"
                />
              </svg>
              <span className="text-gray-600 text-lg">{location}</span>
            </div>
          )}
        </div>
      </div>
      <div className="flex flex-col justify-center items-end gap-2">
        {!isSubscribed && (
          <div className="relative">
            <button
              className="group relative flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 cursor-pointer"
              onClick={() => {
                onNotificationClick();
                setIsSubscribed(true);
              }}
            >
              <div className="relative">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="group-hover:animate-pulse"
                >
                  <path d="M10.268 21a2 2 0 0 0 3.464 0" />
                  <path d="M3.262 15.326A1 1 0 0 0 4 17h16a1 1 0 0 0 .74-1.673C19.41 13.956 18 12.499 18 8A6 6 0 0 0 6 8c0 4.499-1.411 5.956-2.738 7.326" />
                </svg>
                {/* Notification dot */}
                <div className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full animate-ping"></div>
                <div className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full"></div>
              </div>
              <span className="text-sm font-medium hidden sm:inline">
                알림 받기
              </span>
            </button>

            {/* Tooltip */}
            <div className="absolute bottom-full right-0 mb-2 px-3 py-1 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 whitespace-nowrap pointer-events-none">
              날씨 알림을 받으려면 클릭하세요
              <div className="absolute top-full right-4 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
            </div>
          </div>
        )}
        <ChatAssistant />
      </div>
    </div>
  );
}
