import { useState, FormEvent, KeyboardEvent } from "react";

type ChatInputProps = {
  onSendMessage: (message: string) => void;
  placeholder?: string;
  disabled?: boolean;
};

export function ChatInput({
  onSendMessage,
  placeholder = "메시지를 입력하세요...",
  disabled = false,
}: ChatInputProps) {
  const [message, setMessage] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message);
      setMessage("");
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-start gap-2">
      <div className="flex-1 relative">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-400/50 focus:border-blue-400/50 resize-none min-h-[50px] max-h-[150px] overflow-auto placeholder-gray-500 text-gray-800 shadow-sm"
          rows={2}
          autoFocus
        />
      </div>
      <button
        type="submit"
        disabled={!message.trim() || disabled}
        className={`p-2 rounded-full transition-colors w-10 h-10 flex items-center justify-center backdrop-blur-sm border shadow-sm ${
          !message.trim() || disabled
            ? "bg-gray-300/50 text-gray-500 border-gray-300/30"
            : "bg-blue-500/80 text-white hover:bg-blue-600/80 border-blue-400/30"
        }`}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.5}
          stroke="currentColor"
          className="w-5 h-5"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5"
          />
        </svg>
      </button>
    </form>
  );
}
