import { useState, useEffect, useRef } from "react";
import { ChatMessage } from "../components/chat-message";
import { ChatInput } from "../components/chat-input";

type Message = {
  id: string;
  message: string;
  sender: "user" | "assistant";
  timestamp: Date;
};

export function Chat() {
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

  return (
    <div className="flex flex-col h-full w-full">
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

      <div className="border-t border-gray-200 p-4 bg-gray-50">
        <ChatInput
          onSendMessage={handleSendMessage}
          disabled={status === "sending" || status === "responding"}
        />
      </div>
    </div>
  );
}
