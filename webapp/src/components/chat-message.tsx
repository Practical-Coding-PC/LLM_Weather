import { FC } from "react";

interface ChatMessageProps {
  message: string;
  timestamp: Date;
  sender: "user" | "assistant";
}

export const ChatMessage: FC<ChatMessageProps> = ({
  message,
  timestamp,
  sender,
}) => {
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
            className={`rounded-lg px-4 py-2 ${
              sender === "user"
                ? "bg-blue-500 text-white rounded-tr-none"
                : "bg-gray-200 text-gray-800 rounded-tl-none"
            }`}
          >
            <p className="break-words">{message}</p>
          </div>

          <div
            className={`text-xs text-gray-500 mt-1 ${
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
