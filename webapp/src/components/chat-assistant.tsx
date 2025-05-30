import React from "react";
import Link from "next/link";

type ChatAssistantProps = {
  onClick: () => void;
};

export function ChatAssistant({ onClick }: ChatAssistantProps) {
  return (
    <div className="flex justify-end p-6">
      <Link href="/chat">
        <div
          className="w-14 h-14 bg-white/40 backdrop-blur-sm border border-white/30 rounded-full flex items-center justify-center cursor-pointer hover:bg-white/60 transition-all duration-200 shadow-lg hover:shadow-xl"
          onClick={onClick}
        >
          <svg
            width="26"
            height="26"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <circle
              cx="12"
              cy="12"
              r="10"
              stroke="#374151"
              strokeWidth="2"
              fill="none"
            />
            <path
              d="M8 14C8 14 10 16 12 16C14 16 16 14 16 14"
              stroke="#374151"
              strokeWidth="2"
            />
            <circle cx="8" cy="10" r="1.5" fill="#374151" />
            <circle cx="16" cy="10" r="1.5" fill="#374151" />
          </svg>
        </div>
      </Link>
    </div>
  );
}
