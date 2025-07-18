import React from "react";
import Link from "next/link";

interface ChatAssistantProps {
  isSticky?: boolean;
}

export function ChatAssistant({ isSticky = false }: ChatAssistantProps) {
  return (
    <Link href="/chat">
      <div
        className={`${
          isSticky
            ? "bg-white/20 backdrop-blur-md rounded-xl"
            : "bg-white/10 backdrop-blur-md rounded-2xl"
        } flex items-center justify-between px-2 cursor-pointer hover:bg-white/30 transition-all duration-300 shadow hover:shadow-lg hover:scale-101 transform border border-gray-200`}
      >
        <div className="flex items-center gap-1">
          <div
            className={`${
              isSticky ? "w-8 h-8" : "w-10 h-10"
            } bg-white/20 rounded-full flex items-center justify-center backdrop-blur-sm`}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width={isSticky ? "20" : "24"}
              height={isSticky ? "20" : "24"}
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M12 8V4H8" />
              <rect width="16" height="12" x="4" y="8" rx="2" />
              <path d="M2 14h2" />
              <path d="M20 14h2" />
              <path d="M15 13v2" />
              <path d="M9 13v2" />
            </svg>
          </div>
          <div className="text-slate-700">
            <div className={`${isSticky ? "text-xs" : "text-sm"} font-medium`}>
              챗봇
            </div>
          </div>
        </div>
        <div className="text-slate-600">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width={isSticky ? "18" : "20"}
            height={isSticky ? "18" : "20"}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="m9 18 6-6-6-6" />
          </svg>
        </div>
      </div>
    </Link>
  );
}
