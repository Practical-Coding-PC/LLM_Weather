import { useState, useEffect, useRef } from "react";
import { ChatMessage } from "../components/chat-message";
import { ChatInput } from "../components/chat-input";
import { useWeather } from "../lib/weather-context";
import {
  sendChatMessage,
  getChatMessages,
  type ChatMessage as APIChatMessage,
} from "../lib/chat-api";

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

// API 메시지를 UI 메시지로 변환하는 함수
const convertAPIMessageToUIMessage = (apiMessage: APIChatMessage): Message => ({
  id: apiMessage.id.toString(),
  message: apiMessage.content,
  sender: apiMessage.role,
  timestamp: new Date(apiMessage.created_at),
});

export function Chat() {
  const { currentTemp: weatherTemp, userId } = useWeather();
  const [status, setStatus] = useState<"idle" | "sending" | "responding">(
    "idle"
  );
  const [messages, setMessages] = useState<Message[]>([]);
  const [chatId, setChatId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 컴포넌트 마운트 시 초기 메시지 설정
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([
        {
          id: "welcome",
          message:
            "안녕하세요! 날씨와 CCTV 정보에 대해 궁금한 것이 있으시면 언제든 물어보세요. 🌤️📹",
          sender: "assistant",
          timestamp: new Date(),
        },
      ]);
    }
  }, [messages.length]);

  // chatId가 있으면 이전 대화 기록 로드
  useEffect(() => {
    const loadChatHistory = async () => {
      if (chatId && userId) {
        try {
          setIsLoading(true);
          const response = await getChatMessages(chatId);
          const uiMessages = response.messages.map(
            convertAPIMessageToUIMessage
          );
          setMessages(uiMessages);
        } catch (err) {
          console.error("대화 기록 로드 실패:", err);
          setError("대화 기록을 불러오는데 실패했습니다.");
        } finally {
          setIsLoading(false);
        }
      }
    };

    loadChatHistory();
  }, [chatId, userId]);

  const handleSendMessage = async (text: string) => {
    if (!userId) {
      setError("사용자 ID가 설정되지 않았습니다.");
      return;
    }

    setStatus("sending");
    setError(null);

    const newMessage: Message = {
      id: Date.now().toString(),
      message: text,
      sender: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, newMessage]);
    setStatus("responding");

    try {
      const response = await sendChatMessage({
        message: text,
        user_id: userId.toString(),
        chat_id: chatId || undefined,
      });

      // 첫 번째 메시지인 경우 chatId 설정
      if (!chatId) {
        setChatId(response.chat_id);
      }

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        message: response.reply,
        sender: "assistant",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, botMessage]);
      setStatus("idle");
    } catch (err) {
      console.error("메시지 전송 실패:", err);
      setError(
        err instanceof Error ? err.message : "메시지 전송에 실패했습니다."
      );

      // 에러 발생 시 사용자 메시지는 그대로 두고 에러 메시지 추가
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        message: "죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해주세요.",
        sender: "assistant",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
      setStatus("idle");
    }
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
            날씨 & CCTV 챗봇
          </h1>
          <p className="text-sm text-gray-600 text-center mt-1">
            날씨 정보와 CCTV 영상을 확인하세요
          </p>
          {/* 개발용: userId 표시 */}
          {userId && (
            <p className="text-xs text-gray-500 text-center mt-1">
              User ID: {userId}
            </p>
          )}
          {/* 에러 메시지 표시 */}
          {error && (
            <div className="mt-2 p-2 bg-red-100/80 text-red-800 text-sm rounded border border-red-200/50">
              {error}
            </div>
          )}
        </div>
      </div>

      {/* 메시지 영역 */}
      <div className="flex-1 p-4 overflow-y-auto">
        {isLoading ? (
          <div className="flex justify-center items-center h-full">
            <div className="text-gray-600">대화 기록을 불러오는 중...</div>
          </div>
        ) : (
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
                message="답변을 생성하고 있습니다..."
                sender="assistant"
                timestamp={new Date()}
              />
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* 입력 영역 */}
      <div className="border-t border-white/20 p-4">
        <div className="bg-white/30 backdrop-blur-sm rounded-lg p-4">
          <ChatInput
            onSendMessage={handleSendMessage}
            disabled={
              status === "sending" || status === "responding" || !userId
            }
            placeholder={
              !userId
                ? "사용자 ID를 설정 중입니다..."
                : "날씨나 CCTV에 대해 궁금한 것을 물어보세요..."
            }
          />
          {status !== "idle" && (
            <div className="text-xs text-gray-600 mt-2 text-center">
              {status === "sending" && "메시지 전송 중..."}
              {status === "responding" && "응답 대기 중..."}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
