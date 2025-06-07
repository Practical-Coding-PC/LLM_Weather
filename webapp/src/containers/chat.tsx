import { useState, useEffect, useRef } from "react";
import { ChatMessage } from "../components/chat-message";
import { ChatInput } from "../components/chat-input";
import { useWeather } from "../lib/weather-context";
import {
  sendChatMessage,
  getChatMessages,
  type ChatMessage as APIChatMessage,
} from "../lib/chat-api";
import {
  getUltraShortTermWeather,
  getShortTermWeather,
  type UltraShortTermWeatherResponse,
  type ShortTermWeatherResponse,
  type WeatherApiItem,
} from "../lib/weather-api";
import { getTemperatureGradient } from "../lib/utils";
import { ArrowLeftIcon } from "lucide-react";
import { useRouter } from "next/navigation";

// CCTV 데이터 타입 정의
type CCTVData = {
  [key: string]: unknown;
};

type Message = {
  id: string;
  message: string;
  sender: "user" | "assistant";
  timestamp: Date;
  cctvData?: CCTVData; // CCTV 데이터를 저장할 필드 추가
};

// Python 딕셔너리 형식을 JSON으로 변환하는 함수
const convertPythonDictToJSON = (pythonDict: string): string => {
  return pythonDict
    .replace(/'/g, '"') // 작은따옴표를 큰따옴표로 변경
    .replace(/True/g, "true") // Python True를 JavaScript true로
    .replace(/False/g, "false") // Python False를 JavaScript false로
    .replace(/None/g, "null"); // Python None을 JavaScript null로
};

// API 메시지를 UI 메시지로 변환하는 함수
const convertAPIMessageToUIMessage = (apiMessage: APIChatMessage): Message => {
  let messageContent = apiMessage.content;
  let cctvData = undefined;

  // CCTV 데이터 응답 처리
  if (apiMessage.content.startsWith("cctv_data:")) {
    try {
      const rawDataString = apiMessage.content.substring("cctv_data:".length);
      const jsonString = convertPythonDictToJSON(rawDataString);
      cctvData = JSON.parse(jsonString);
      messageContent = JSON.stringify(cctvData, null, 2); // 일단 문자열로 표시
    } catch (parseError) {
      console.error("CCTV 데이터 파싱 실패:", parseError);
      console.error("원본 데이터:", apiMessage.content);
      messageContent = "CCTV 데이터를 처리하는 중 오류가 발생했습니다.";
    }
  }

  return {
    id: apiMessage.id.toString(),
    message: messageContent,
    sender: apiMessage.role,
    timestamp: new Date(apiMessage.created_at),
    cctvData: cctvData,
  };
};

// 시간대별 날씨 데이터 타입
interface TimeSlot {
  time: string;
  temp: number;
  sky: number; // 하늘상태
  pty: number; // 강수형태
  windU: number; // 동서바람성분 (UUU)
  windV: number; // 남북바람성분 (VVV)
  humidity: number; // 습도 (REH)
}

// 시간 포맷팅 함수 (HHMM -> H PM/AM)
const formatTime = (timeString: string): string => {
  const hour = parseInt(timeString.substring(0, 2));
  const period = hour >= 12 ? "PM" : "AM";
  const displayHour = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour;
  return `${displayHour} ${period}`;
};

// 날짜와 시간을 조합하여 정렬 키 생성
const getDateTimeKey = (fcstDate: string, fcstTime: string): string => {
  return `${fcstDate}_${fcstTime}`;
};

// API 데이터를 TimeSlot 배열로 변환 (초단기 + 단기 예보 조합)
const processWeatherData = (
  ultraShortTermData: WeatherApiItem[],
  shortTermData: WeatherApiItem[]
): TimeSlot[] => {
  // 모든 데이터를 조합
  const allData = [...ultraShortTermData, ...shortTermData];

  // 시간별로 그룹화 (날짜_시간을 키로 사용)
  const timeGroups: { [key: string]: { [category: string]: string } } = {};

  allData.forEach((item) => {
    const timeKey = getDateTimeKey(item.fcstDate, item.fcstTime);
    if (!timeGroups[timeKey]) {
      timeGroups[timeKey] = {};
    }
    // 같은 시간대에 초단기와 단기 데이터가 모두 있는 경우, 초단기 데이터 우선
    if (!timeGroups[timeKey][item.category]) {
      timeGroups[timeKey][item.category] = item.fcstValue;
    }
  });

  // TimeSlot 배열 생성
  const timeSlots: TimeSlot[] = Object.entries(timeGroups)
    .map(([dateTimeKey, data]) => {
      const [, fcstTime] = dateTimeKey.split("_");
      return {
        time: formatTime(fcstTime),
        temp: parseInt(data.TMP || data.T1H || "0"), // 단기예보는 TMP, 초단기는 T1H
        sky: parseInt(data.SKY || "1"), // 하늘상태 (기본값: 맑음)
        pty: parseInt(data.PTY || "0"), // 강수형태 (기본값: 없음)
        windU: parseInt(data.UUU || "0"), // 동서바람성분
        windV: parseInt(data.VVV || "0"), // 남북바람성분
        humidity: parseInt(data.REH || "50"), // 습도 (기본값: 50%)
      };
    })
    .sort((a, b) => {
      // 시간순 정렬을 위해 원본 날짜_시간 문자열 사용
      const timeKeyA =
        Object.keys(timeGroups).find((key) => {
          const [, fcstTime] = key.split("_");
          return formatTime(fcstTime) === a.time;
        }) || "";
      const timeKeyB =
        Object.keys(timeGroups).find((key) => {
          const [, fcstTime] = key.split("_");
          return formatTime(fcstTime) === b.time;
        }) || "";
      return timeKeyA.localeCompare(timeKeyB);
    });

  // 최대 12시간 데이터 반환 (초단기 6시간 + 단기 6시간)
  return timeSlots.slice(0, 12);
};

export function Chat() {
  const { currentTemp: weatherTemp, userId, coordinates, setCurrentTemp, setLocation: setWeatherLocation, setCoordinates } = useWeather();
  const [status, setStatus] = useState<"idle" | "sending" | "responding">(
    "idle"
  );
  const [messages, setMessages] = useState<Message[]>([]);
  const [chatId, setChatId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  
  // 날씨 데이터 상태 추가
  const [weatherData, setWeatherData] = useState<{
    location: string;
    currentTemp: string;
    timeSlots: TimeSlot[];
  } | null>(null);
  const [isLoadingWeather, setIsLoadingWeather] = useState(false);
  const [weatherError, setWeatherError] = useState<string | null>(null);
  const [locationError, setLocationError] = useState<string | null>(null);
  
  // 발표용 날씨 오버라이드 상태
  const [weatherOverride, setWeatherOverride] = useState<{
    enabled: boolean;
    sky: number;
    pty: number;
    temp: number;
  }>({ enabled: false, sky: 1, pty: 0, temp: 22 });
  
  const [showControls, setShowControls] = useState(false);

  // 위치 정보 가져오기 및 날씨 데이터 가져오기 통합 Effect
  useEffect(() => {
    const fetchAndSetWeatherData = async (lat: number, lon: number) => {
      setIsLoadingWeather(true);
      setWeatherError(null);
      try {
        // API 호출 (새로운 함수 사용)
        const ultraShortTermData: UltraShortTermWeatherResponse =
          await getUltraShortTermWeather(lat, lon);
        const shortTermData: ShortTermWeatherResponse =
          await getShortTermWeather(lat, lon);

        // API 응답에서 requestCode 확인
        if (
          ultraShortTermData.requestCode !== "200" ||
          shortTermData.requestCode !== "200"
        ) {
          throw new Error(
            `API error with code: ${ultraShortTermData.requestCode} or ${shortTermData.requestCode}`
          );
        }

        const timeSlots = processWeatherData(
          ultraShortTermData.items,
          shortTermData.items
        );
        const currentTemp =
          timeSlots.length > 0 ? `${timeSlots[0].temp}°C` : "N/A";
        const currentTempNumber = timeSlots.length > 0 ? timeSlots[0].temp : 20;

        // 단기 데이터에서 location 정보 추출
        const locationName = ultraShortTermData.location || "현재 위치";

        setCurrentTemp(currentTempNumber);
        setWeatherLocation(locationName);

        setWeatherData({
          location: locationName,
          currentTemp,
          timeSlots,
        });
      } catch (error) {
        console.error("날씨 데이터 가져오기 실패:", error);
        setWeatherError(
          error instanceof Error
            ? error.message
            : "날씨 데이터를 가져올 수 없습니다."
        );
        setWeatherData(null);
      } finally {
        setIsLoadingWeather(false);
      }
    };

    if (!navigator.geolocation) {
      setLocationError("이 브라우저는 위치 서비스를 지원하지 않습니다.");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const newLocation = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        };
        setCoordinates(newLocation);
        fetchAndSetWeatherData(newLocation.latitude, newLocation.longitude);
      },
      (error) => {
        let errorMessage = "위치를 가져올 수 없습니다.";
        switch (error.code) {
          case error.PERMISSION_DENIED:
            errorMessage = "위치 접근이 거부되었습니다.";
            break;
          case error.POSITION_UNAVAILABLE:
            errorMessage = "위치 정보를 사용할 수 없습니다.";
            break;
          case error.TIMEOUT:
            errorMessage = "위치 요청 시간이 초과되었습니다.";
            break;
        }
        setLocationError(errorMessage);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 300000, // 5분간 캐시된 위치 사용
      }
    );
  }, [setCurrentTemp, setWeatherLocation, setCoordinates]);

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
        } finally {
          setIsLoading(false);
        }
      }
    };

    loadChatHistory();
  }, [chatId, userId]);

  const handleSendMessage = async (text: string) => {
    if (Number.isNaN(userId)) {
      return;
    }

    setStatus("sending");

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
        user_id: userId?.toString() || "",
        chat_id: chatId || undefined,
        latitude: coordinates?.latitude || 0,
        longitude: coordinates?.longitude || 0,
      });

      // 첫 번째 메시지인 경우 chatId 설정
      if (!chatId) {
        setChatId(response.chat_id);
      }

      // CCTV 데이터 응답 처리
      let botMessageContent = response.reply;
      let cctvData = undefined;

      if (response.reply.startsWith("cctv_data:")) {
        try {
          const rawDataString = response.reply.substring("cctv_data:".length);
          const jsonString = convertPythonDictToJSON(rawDataString);
          cctvData = JSON.parse(jsonString);
          botMessageContent = JSON.stringify(cctvData, null, 2); // 일단 문자열로 표시
        } catch (parseError) {
          console.error("CCTV 데이터 파싱 실패:", parseError);
          console.error("원본 데이터:", response.reply);
          botMessageContent = "CCTV 데이터를 처리하는 중 오류가 발생했습니다.";
        }
      }

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        message: botMessageContent,
        sender: "assistant",
        timestamp: new Date(),
        cctvData: cctvData,
      };

      setMessages((prev) => [...prev, botMessage]);
      setStatus("idle");
    } catch (err) {
      console.error("메시지 전송 실패:", err);
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

  // 현재 날씨 상태 (첫 번째 타임슬롯에서 가져오기 또는 오버라이드)
  const currentWeather = weatherOverride.enabled 
    ? weatherOverride 
    : (weatherData?.timeSlots[0] || {
        temp: 25, // 테스트용 기본값
        sky: 4,   // 4: 흐림 (테스트)
        pty: 0    // 0: 비/눈 없음
      });

  // 날씨에 따른 배경 색상 계산 (메인 페이지와 동일)
  const getWeatherBackground = () => {
    const weather = currentWeather;
    
    if (weather.pty > 0) {
      // 비나 눈이 올 때 - 진한 회색
      return "from-gray-600/60 via-slate-400/70 to-blue-300/80";
    }
    
    if (weather.sky >= 3) {
      // 구름많음, 흐림 - 회색조
      return "from-gray-400/60 via-slate-300/70 to-gray-200/80";
    }
    
    // 맑음이나 구름조금일 때는 기온에 따른 색상
    if (weather.temp >= 30) return "from-red-200/80 via-orange-300/80 to-yellow-200/80";
    if (weather.temp >= 25) return "from-orange-200/80 via-yellow-300/80 to-green-200/80";
    if (weather.temp >= 20) return "from-yellow-200/80 via-green-300/80 to-blue-200/80";
    if (weather.temp >= 15) return "from-green-200/80 via-blue-300/80 to-indigo-200/80";
    if (weather.temp >= 10) return "from-blue-200/80 via-indigo-300/80 to-purple-200/80";
    if (weather.temp >= 5) return "from-indigo-200/80 via-purple-300/80 to-blue-200/80";
    return "from-purple-200/80 via-blue-300/80 to-indigo-200/80";
  };

  return (
    <div
      className={`flex flex-col h-full w-full bg-gradient-to-br ${getWeatherBackground()} transition-all duration-1000 ease-in-out relative`}
    >
      {/* 발표용 컨트롤 토글 버튼 */}
      <button
        onClick={() => setShowControls(!showControls)}
        className="fixed top-4 right-4 z-50 bg-black/20 hover:bg-black/30 text-white p-2 rounded-full transition-all"
        title="발표용 컴트롤"
      >
        Test
      </button>

      {/* 발표용 컴트롤 패널 */}
      {showControls && (
        <div className="fixed top-16 right-4 z-50 bg-white/95 backdrop-blur-sm p-4 rounded-lg shadow-lg border max-w-xs">
          <div className="space-y-3">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={weatherOverride.enabled}
                onChange={(e) => setWeatherOverride(prev => ({ ...prev, enabled: e.target.checked }))}
                className="rounded"
              />
              <span className="text-sm font-medium">데모 모드</span>
            </label>

            {weatherOverride.enabled && (
              <>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    기온: {weatherOverride.temp}°C
                  </label>
                  <input
                    type="range"
                    min="-10"
                    max="40"
                    value={weatherOverride.temp}
                    onChange={(e) => setWeatherOverride(prev => ({ ...prev, temp: parseInt(e.target.value) }))}
                    className="w-full h-1 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    하늘: {['', '맑음', '구름조금', '구름많음', '흐림'][weatherOverride.sky]}
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="4"
                    value={weatherOverride.sky}
                    onChange={(e) => setWeatherOverride(prev => ({ ...prev, sky: parseInt(e.target.value) }))}
                    className="w-full h-1 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    강수: {['없음', '비', '비/눈', '눈', '소나기'][weatherOverride.pty]}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="4"
                    value={weatherOverride.pty}
                    onChange={(e) => setWeatherOverride(prev => ({ ...prev, pty: parseInt(e.target.value) }))}
                    className="w-full h-1 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  />
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* 날씨 애니메이션 요소들 */}
      {currentWeather.sky <= 2 && currentWeather.pty === 0 && (
        // 맑은 날씨일 때 태양
        <div className="absolute top-12 right-8 w-16 h-16">
          <div className="w-full h-full bg-yellow-300 rounded-full shadow-lg animate-pulse opacity-90">
            <div className="w-full h-full bg-gradient-to-br from-yellow-200 to-orange-300 rounded-full"></div>
          </div>
          {/* 태양 광선 */}
          {[...Array(8)].map((_, i) => (
            <div
              key={i}
              className="absolute w-0.5 h-4 bg-yellow-300 opacity-60 animate-pulse"
              style={{
                top: '50%',
                left: '50%',
                transformOrigin: '50% 24px',
                transform: `translate(-50%, -50%) rotate(${i * 45}deg)`,
                animationDelay: `${i * 0.3}s`
              }}
            />
          ))}
        </div>
      )}
      
      {currentWeather.sky >= 3 && (
        // 구름많음/흐림일 때 구름
        <>
          <div className="absolute top-16 left-8 w-16 h-10 bg-white/70 rounded-full animate-bounce shadow-md" style={{animationDelay: '0s', animationDuration: '4s'}}>
            <div className="absolute inset-0 bg-gray-100/50 rounded-full"></div>
          </div>
          <div className="absolute top-20 right-12 w-12 h-8 bg-white/60 rounded-full animate-bounce shadow-md" style={{animationDelay: '1s', animationDuration: '5s'}}>
            <div className="absolute inset-0 bg-gray-100/40 rounded-full"></div>
          </div>
          <div className="absolute top-32 left-16 w-14 h-9 bg-white/80 rounded-full animate-bounce shadow-md" style={{animationDelay: '2s', animationDuration: '6s'}}>
            <div className="absolute inset-0 bg-gray-100/60 rounded-full"></div>
          </div>
          <div className="absolute top-24 right-6 w-10 h-7 bg-white/50 rounded-full animate-bounce shadow-md" style={{animationDelay: '1.5s', animationDuration: '4.5s'}}>
            <div className="absolute inset-0 bg-gray-100/30 rounded-full"></div>
          </div>
        </>
      )}
      
      {currentWeather.pty > 0 && (
        // 비/눈이 올 때 효과
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          {[...Array(30)].map((_, i) => (
            <div
              key={i}
              className={`absolute ${currentWeather.pty === 3 ? 'w-1 h-1 bg-white rounded-full' : 'w-0.5 h-6 bg-blue-400 opacity-70'} animate-pulse`}
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 80 + 10}%`,
                animationDelay: `${Math.random() * 2}s`,
                animationDuration: `${1 + Math.random() * 2}s`
              }}
            />
          ))}
        </div>
      )}

      {/* 헤더 영역 */}
      <div className="relative z-10">
        <div className="flex justify-between p-2 items-center">
          <button
            className="p-2 cursor-pointer"
            onClick={() => {
              router.back();
            }}
          >
            <ArrowLeftIcon className="size-6" />
          </button>
          <h1 className="text-lg font-semibold text-gray-600">
            날씨 & CCTV 챗봇
          </h1>
          <div className="w-16" />
        </div>
      </div>

      {/* 메시지 영역 */}
      <div className="flex-1 p-4 overflow-y-auto relative z-10">
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
                cctvData={msg.cctvData}
              />
            ))}
            {status === "responding" && (
              <ChatMessage
                sender="assistant"
                timestamp={new Date()}
                typing={true}
              />
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* 입력 영역 */}
      <div className="relative z-10">
        <ChatInput
        onSendMessage={handleSendMessage}
        disabled={
          status === "sending" ||
          status === "responding" ||
          Number.isNaN(userId)
        }
        placeholder={
          Number.isNaN(userId)
            ? "사용자 ID를 설정 중입니다..."
            : "날씨나 CCTV에 대해 궁금한 것을 물어보세요..."
        }
        />
      </div>
    </div>
  );
}
