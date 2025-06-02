import { ChatAssistant } from "./chat-assistant";

type WeatherHeaderProps = {
  currentTemp: string;
};

export function WeatherHeader({ currentTemp }: WeatherHeaderProps) {
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
        </div>
      </div>
      <div className="flex justify-end items-center">
        <ChatAssistant />
      </div>
    </div>
  );
}
