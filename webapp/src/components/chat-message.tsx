import { FC, useState } from "react";

// CCTV 데이터 타입 정의
type CCTVData = {
  cctvname?: string;
  cctvurl?: string;
  coordx?: number;
  coordy?: number;
  distance?: number;
  target_location?: string;
  [key: string]: unknown;
};

interface ChatMessageProps {
  message?: string;
  timestamp: Date;
  sender: "user" | "assistant";
  cctvData?: CCTVData;
  typing?: boolean;
}

export const ChatMessage: FC<ChatMessageProps> = ({
  message,
  timestamp,
  sender,
  cctvData,
  typing,
}) => {
  const [videoError, setVideoError] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const handleVideoLoad = () => {
    setIsLoading(false);
    setVideoError(false);
  };

  const handleVideoError = () => {
    setIsLoading(false);
    setVideoError(true);
  };

  if (typing) {
    return (
      <div
        className={`flex ${
          sender === "user" ? "justify-end" : "justify-start"
        } mb-4`}
      >
        <div
          className={`flex ${
            sender === "user" ? "flex-row-reverse" : "flex-row"
          } max-w-[80%]`}
        >
          <div>
            <div
              className={`rounded-lg px-4 py-3 backdrop-blur-sm border ${
                sender === "user"
                  ? "bg-blue-500/80 text-white rounded-tr-none border-blue-400/30"
                  : "bg-white/40 text-gray-800 rounded-tl-none border-white/30"
              } shadow-sm flex items-center space-x-1`}
            >
              <span className="dot bg-gray-200 animate-bounce" />
              <span className="dot bg-gray-200 animate-bounce delay-150" />
              <span className="dot bg-gray-200 animate-bounce delay-300" />
            </div>
            <div
              className={`text-xs text-gray-600 mt-1 ${
                sender === "user" ? "text-right" : "text-left"
              }`}
            >
              {timestamp.toLocaleTimeString("ko-KR", {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`flex ${
        sender === "user" ? "justify-end" : "justify-start"
      } mb-4`}
    >
      <div
        className={`flex ${
          sender === "user" ? "flex-row-reverse" : "flex-row"
        } max-w-[80%]`}
      >
        <div>
          <div
            className={`rounded-lg px-4 py-3 backdrop-blur-sm border ${
              sender === "user"
                ? "bg-blue-500/80 text-white rounded-tr-none border-blue-400/30"
                : "bg-white/40 text-gray-800 rounded-tl-none border-white/30"
            } shadow-sm`}
          >
            {/* CCTV 데이터가 있으면 메시지 숨기기 */}
            {!(cctvData && cctvData.cctvurl) && (
              <p className="break-words">{message}</p>
            )}

            {cctvData && cctvData.cctvurl && (
              <div className="mt-4 space-y-3">
                {/* CCTV 정보 */}
                <div className="text-sm">
                  <h4 className="font-semibold text-gray-700 mb-2">
                    📹 CCTV 정보
                  </h4>
                  {cctvData.cctvname && (
                    <p className="text-gray-600 mb-1">
                      <span className="font-medium">위치:</span>{" "}
                      {cctvData.cctvname}
                    </p>
                  )}
                  {cctvData.distance && (
                    <p className="text-gray-600 mb-2">
                      <span className="font-medium">
                        현재 위치로부터의 거리:
                      </span>{" "}
                      {cctvData.distance.toFixed(2)}km
                    </p>
                  )}
                </div>

                {/* 비디오 플레이어 */}
                <div className="relative">
                  {isLoading && (
                    <div className="absolute inset-0 flex items-center justify-center bg-gray-100 rounded">
                      <div className="text-gray-500 text-sm">
                        동영상 로딩 중...
                      </div>
                    </div>
                  )}

                  {videoError ? (
                    <div className="bg-gray-100 rounded p-4 text-center">
                      <p className="text-gray-500 text-sm mb-2">
                        동영상을 로드할 수 없습니다
                      </p>
                      <a
                        href={cctvData.cctvurl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-500 hover:text-blue-700 text-sm underline"
                      >
                        직접 링크에서 보기 →
                      </a>
                    </div>
                  ) : (
                    <video
                      className="w-full max-w-md rounded border"
                      controls
                      autoPlay
                      muted
                      onLoadedData={handleVideoLoad}
                      onError={handleVideoError}
                      style={{ aspectRatio: "16/9" }}
                    >
                      <source src={cctvData.cctvurl} type="video/mp4" />
                      <source
                        src={cctvData.cctvurl}
                        type="application/x-mpegURL"
                      />
                      <source src={cctvData.cctvurl} type="video/webm" />
                      브라우저가 비디오를 지원하지 않습니다.
                    </video>
                  )}
                </div>
              </div>
            )}

            {cctvData && !cctvData.cctvurl && (
              <div className="mt-2 text-xs text-gray-600">
                <p>CCTV 데이터: {JSON.stringify(cctvData)}</p>
              </div>
            )}
          </div>

          <div
            className={`text-xs text-gray-600 mt-1 ${
              sender === "user" ? "text-right" : "text-left"
            }`}
          >
            {timestamp.toLocaleTimeString("ko-KR", {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
