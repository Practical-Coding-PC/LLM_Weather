// API 기본 설정
const API_BASE_URL =
  typeof window !== "undefined"
    ? process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
    : "http://localhost:8000";

export interface ChatRequest {
  message: string;
  user_id: string;
  chat_id?: number;
}

export interface ChatResponse {
  reply: string;
  chat_id: number;
}

export interface ChatMessage {
  id: number;
  chat_id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface Chat {
  id: number;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface HealthCheckResponse {
  status: string;
  gemini_api: string;
  kma_api: string;
  cctv_api: string;
  supported_locations: string[];
}

export interface SupportedLocationsResponse {
  locations: string[];
  details: Record<string, { name: string }>;
}

interface ErrorResponse {
  detail: string;
}

// 채팅 메시지 전송
export async function sendChatMessage(
  request: ChatRequest
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorData = (await response
      .json()
      .catch(() => ({ detail: "Unknown error" }))) as ErrorResponse;
    throw new Error(errorData.detail || "Failed to send message");
  }

  return response.json();
}

// 채팅 메시지 기록 조회
export async function getChatMessages(
  chatId: number
): Promise<{ chat_id: number; messages: ChatMessage[] }> {
  const response = await fetch(`${API_BASE_URL}/api/chat/${chatId}/messages`);

  if (!response.ok) {
    throw new Error("Failed to fetch chat messages");
  }

  return response.json();
}

// 사용자의 채팅 목록 조회
export async function getUserChats(
  userId: string
): Promise<{ user_id: string; chats: Chat[] }> {
  const response = await fetch(`${API_BASE_URL}/api/chats/${userId}`);

  if (!response.ok) {
    throw new Error("Failed to fetch user chats");
  }

  return response.json();
}

// 서버 상태 확인
export async function getHealthCheck(): Promise<HealthCheckResponse> {
  const response = await fetch(`${API_BASE_URL}/health`);

  if (!response.ok) {
    throw new Error("Failed to check server health");
  }

  return response.json();
}

// 지원되는 지역 목록 조회
export async function getSupportedLocations(): Promise<SupportedLocationsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/locations`);

  if (!response.ok) {
    throw new Error("Failed to fetch supported locations");
  }

  return response.json();
}
