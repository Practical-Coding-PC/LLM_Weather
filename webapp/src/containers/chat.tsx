import { useState, useEffect, useRef } from "react";
import { ChatMessage } from "../components/chat-message";
import { ChatInput } from "../components/chat-input";
import { useWeather } from "../lib/weather-context";

type Message = {
  id: string;
  message: string;
  sender: "user" | "assistant";
  timestamp: Date;
};

// 기온에 따른 배경 그라데이션 색상 (weather-dashboard와 동일)
const getTemperatureGradient = (temp: number): string => {
  if (temp >= 30) return "from-red-50 via-orange-25 to-white";
  if (temp >= 25) return "from-orange-50 via-yellow-25 to-white";
  if (temp >= 20) return "from-yellow-50 via-green-25 to-white";
  if (temp >= 15) return "from-green-50 via-blue-25 to-white";
  if (temp >= 10) return "from-blue-50 via-indigo-25 to-white";
  if (temp >= 5) return "from-indigo-50 via-purple-25 to-white";
  return "from-purple-50 via-blue-25 to-white";
};

export function Chat() {
  const { currentTemp: weatherTemp, userId } = useWeather();
  const [status, setStatus] = useState<"idle" | "sending" | "responding">(
    "idle"
  );
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "0",
      message: "날씨에 대해 알려줄게요",
      sender: "assistant",
      timestamp: new Date(),
    },
    {
      id: "1",
      message: "오늘 날씨 어때?",
      sender: "user",
      timestamp: new Date(),
    },
    {
      id: "2",
      message: "오늘은 맑고 따뜻해요.",
      sender: "assistant",
      timestamp: new Date(),
    },
    {
      id: "3",
      message: "주말에 등산 갈 계획인데 날씨가 좋았으면 좋겠네.",
      sender: "user",
      timestamp: new Date(),
    },
  ]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // userId가 로드되면 콘솔에 출력
  useEffect(() => {
    if (userId) {
      console.log("Current User ID:", userId);
    }
  }, [userId]);

  const handleSendMessage = (text: string) => {
    setStatus("sending");
    const newMessage: Message = {
      id: Date.now().toString(),
      message: text,
      sender: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, newMessage]);
    setStatus("responding");

    // 여기서 userId를 사용하여 API 호출을 할 수 있습니다
    console.log("Sending message with userId:", userId, "Message:", text);

    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          message: "서버로부터 온 응답이 여기에 들어갈 것입니다...",
          sender: "assistant" as const,
          timestamp: new Date(),
        },
      ]);
      setStatus("idle");
    }, 1000);
  };

  // 자동 스크롤 기능
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Context에서 실제 온도 데이터 사용
  const backgroundGradient = getTemperatureGradient(weatherTemp);

  return (
    <div
      className={`flex flex-col h-full w-full bg-gradient-to-br ${backgroundGradient}`}
    >
      {/* 헤더 영역 */}
      <div className="p-4 border-b border-white/20">
        <div className="bg-white/30 backdrop-blur-sm rounded-lg p-4">
          <h1 className="text-xl font-bold text-gray-800 text-center">
            날씨 챗봇
          </h1>
          <p className="text-sm text-gray-600 text-center mt-1">
            궁금한 날씨 정보를 물어보세요
          </p>
          {/* 개발용: userId 표시 */}
          {userId && (
            <p className="text-xs text-gray-500 text-center mt-1">
              User ID: {userId}
            </p>
          )}
        </div>
      </div>

      {/* 메시지 영역 */}
      <div className="flex-1 p-4 overflow-y-auto">
        <div className="space-y-4">
          {messages.map((msg) => (
            <ChatMessage
              key={msg.id}
              message={msg.message}
              sender={msg.sender}
              timestamp={msg.timestamp}
            />
          ))}
          {status === "responding" && (
            <ChatMessage
              message="..."
              sender="assistant"
              timestamp={new Date()}
            />
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* 입력 영역 */}
      <div className="border-t border-white/20 p-4">
        <div className="bg-white/30 backdrop-blur-sm rounded-lg p-4">
          <ChatInput
            onSendMessage={handleSendMessage}
            disabled={status === "sending" || status === "responding"}
          />
        </div>
      </div>
    </div>
  );
}
