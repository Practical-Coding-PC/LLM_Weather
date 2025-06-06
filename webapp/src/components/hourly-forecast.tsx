import React from "react";
import {
  LineChart,
  Line,
  ResponsiveContainer,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";

type TimeSlot = {
  time: string;
  temp: number;
  sky: number; // 하늘상태
  pty: number; // 강수형태
  windU: number; // 동서바람성분 (UUU)
  windV: number; // 남북바람성분 (VVV)
  humidity: number; // 습도 (REH)
};

type HourlyForecastProps = {
  timeSlots: TimeSlot[];
};

// 하늘상태 코드를 텍스트로 변환
const getSkyConditionText = (sky: number): string => {
  switch (sky) {
    case 1:
      return "맑음";
    case 3:
      return "구름많음";
    case 4:
      return "흐림";
    default:
      return "맑음";
  }
};

// 하늘상태 아이콘
const getSkyIcon = (sky: number): string => {
  switch (sky) {
    case 1:
      return "☀️";
    case 3:
      return "⛅";
    case 4:
      return "☁️";
    default:
      return "☀️";
  }
};

// 강수형태 코드를 텍스트로 변환
const getPrecipitationText = (pty: number): string => {
  switch (pty) {
    case 0:
      return "없음";
    case 1:
      return "비";
    case 2:
      return "비/눈";
    case 3:
      return "눈";
    case 5:
      return "빗방울";
    case 6:
      return "빗방울눈날림";
    case 7:
      return "눈날림";
    default:
      return "없음";
  }
};

// 강수형태 아이콘
const getPrecipitationIcon = (pty: number): string => {
  switch (pty) {
    case 0:
      return "";
    case 1:
      return "🌧️";
    case 2:
      return "🌨️";
    case 3:
      return "❄️";
    case 5:
      return "💧";
    case 6:
      return "🌨️";
    case 7:
      return "❄️";
    default:
      return "";
  }
};

// 바람 방향 계산 (동서바람성분, 남북바람성분으로부터)
const getWindDirection = (windU: number, windV: number): string => {
  if (windU === 0 && windV === 0) return "무풍";

  const angle = Math.atan2(windU, windV) * (180 / Math.PI);
  const direction = (angle + 360) % 360;

  if (direction >= 337.5 || direction < 22.5) return "북풍";
  if (direction >= 22.5 && direction < 67.5) return "북동풍";
  if (direction >= 67.5 && direction < 112.5) return "동풍";
  if (direction >= 112.5 && direction < 157.5) return "남동풍";
  if (direction >= 157.5 && direction < 202.5) return "남풍";
  if (direction >= 202.5 && direction < 247.5) return "남서풍";
  if (direction >= 247.5 && direction < 292.5) return "서풍";
  if (direction >= 292.5 && direction < 337.5) return "북서풍";
  return "무풍";
};

// 바람 속도 계산
const getWindSpeed = (windU: number, windV: number): number => {
  return Math.sqrt(windU * windU + windV * windV);
};

// 기온에 따른 색상 결정 함수 (더 선명한 색상으로 개선)
const getTemperatureColor = (temp: number): string => {
  if (temp >= 30) return "#DC2626"; // 진한 빨간색 (매우 더움)
  if (temp >= 25) return "#EA580C"; // 진한 주황색 (더움)
  if (temp >= 20) return "#D97706"; // 진한 노란색 (따뜻함)
  if (temp >= 15) return "#16A34A"; // 진한 초록색 (적당함)
  if (temp >= 10) return "#2563EB"; // 진한 파란색 (시원함)
  if (temp >= 5) return "#4F46E5"; // 진한 남색 (차가움)
  return "#7C3AED"; // 진한 보라색 (매우 추움)
};

// 온도 범위 라벨
const getTemperatureLabel = (temp: number): string => {
  if (temp >= 30) return "매우 더움";
  if (temp >= 25) return "더움";
  if (temp >= 20) return "따뜻함";
  if (temp >= 15) return "적당함";
  if (temp >= 10) return "시원함";
  if (temp >= 5) return "차가움";
  return "매우 추움";
};

// 전체 데이터의 평균 기온으로 대표 색상 결정
const getAverageTemperatureColor = (timeSlots: TimeSlot[]): string => {
  const avgTemp =
    timeSlots.reduce((sum, slot) => sum + slot.temp, 0) / timeSlots.length;
  return getTemperatureColor(avgTemp);
};

// 커스텀 툴팁 컴포넌트
const CustomTooltip = ({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ value: number; payload: TimeSlot }>;
  label?: string;
}) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const temp = data.temp;
    const color = getTemperatureColor(temp);
    const tempLabel = getTemperatureLabel(temp);
    const windDirection = getWindDirection(data.windU, data.windV);
    const windSpeed = getWindSpeed(data.windU, data.windV);

    return (
      <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200 min-w-[180px]">
        <p className="text-sm font-medium text-gray-600 mb-2">{label}</p>

        <div className="space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500">기온</span>
            <span className="text-lg font-bold" style={{ color }}>
              {temp}°C
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500">하늘</span>
            <span className="text-sm">
              {getSkyIcon(data.sky)} {getSkyConditionText(data.sky)}
            </span>
          </div>

          {data.pty > 0 && (
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-500">강수</span>
              <span className="text-sm">
                {getPrecipitationIcon(data.pty)}{" "}
                {getPrecipitationText(data.pty)}
              </span>
            </div>
          )}

          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500">바람</span>
            <span className="text-sm">
              {windDirection} {windSpeed.toFixed(1)}m/s
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500">습도</span>
            <span className="text-sm">{data.humidity}%</span>
          </div>
        </div>

        <p className="text-xs text-gray-500 mt-2">{tempLabel}</p>
      </div>
    );
  }
  return null;
};

export function HourlyForecast({ timeSlots }: HourlyForecastProps) {
  const lineColor = getAverageTemperatureColor(timeSlots);
  const avgTemp =
    timeSlots.reduce((sum, slot) => sum + slot.temp, 0) / timeSlots.length;
  const minTemp = Math.min(...timeSlots.map((slot) => slot.temp));
  const maxTemp = Math.max(...timeSlots.map((slot) => slot.temp));

  return (
    <div className={`px-6 pb-8`}>
      {/* 온도 범위 및 스크롤 힌트 표시 */}
      <div className="flex justify-between items-center mb-4 pt-4">
        <div className="text-sm font-medium text-gray-700">
          시간별 기온 변화
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 text-xs text-gray-600">
            <span className="flex items-center gap-1">
              <div
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: getTemperatureColor(minTemp) }}
              />
              최저 {minTemp}°
            </span>
            <span className="text-gray-400">|</span>
            <span className="flex items-center gap-1">
              <div
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: getTemperatureColor(maxTemp) }}
              />
              최고 {maxTemp}°
            </span>
          </div>
        </div>
      </div>

      {/* 통합 수평 스크롤 컨테이너 */}
      <div className="relative">
        <div className="overflow-x-auto overflow-y-visible scrollbar-hide">
          <div
            style={{ width: `${timeSlots.length * 80}px`, minWidth: "320px" }}
          >
            {/* 날씨 정보 카드들 */}
            <div className="flex gap-4 pb-4 px-2">
              {timeSlots.map((slot, index) => (
                <div
                  key={`${slot.time}-${index}`}
                  className="flex-shrink-0 w-16 text-center"
                >
                  {/* 날씨 아이콘 */}
                  <div className="text-lg mb-2">
                    {getSkyIcon(slot.sky)}
                    {slot.pty > 0 && (
                      <div className="text-sm">
                        {getPrecipitationIcon(slot.pty)}
                      </div>
                    )}
                  </div>

                  {/* 기온 */}
                  <div
                    className="text-sm font-bold mb-2 drop-shadow-sm"
                    style={{ color: getTemperatureColor(slot.temp) }}
                  >
                    {slot.temp}°
                  </div>

                  {/* 하늘상태 */}
                  <div className="text-xs text-gray-600 mb-1 leading-tight">
                    {getSkyConditionText(slot.sky)}
                  </div>
                </div>
              ))}
            </div>

            {/* 차트 */}
            <div className="mt-6 px-2" style={{ height: "144px" }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={timeSlots}
                  margin={{ top: 10, right: 24, left: 24, bottom: 10 }}
                >
                  <XAxis
                    dataKey="time"
                    axisLine={false}
                    tickLine={false}
                    tick={{ fontSize: 11, fill: "#6B7280", fontWeight: 500 }}
                    interval={0}
                  />
                  <YAxis hide />
                  <Tooltip
                    content={<CustomTooltip />}
                    wrapperStyle={{
                      zIndex: 1000,
                      outline: "none",
                      pointerEvents: "none",
                    }}
                    allowEscapeViewBox={{ x: true, y: true }}
                    position={{ y: -100 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="temp"
                    stroke={lineColor}
                    strokeWidth={3}
                    dot={{
                      fill: lineColor,
                      strokeWidth: 2,
                      stroke: "#fff",
                      r: 4,
                      filter: "drop-shadow(0 2px 4px rgba(0,0,0,0.1))",
                    }}
                    activeDot={{
                      r: 6,
                      fill: lineColor,
                      stroke: "#fff",
                      strokeWidth: 3,
                      filter: "drop-shadow(0 4px 8px rgba(0,0,0,0.2))",
                    }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* 습도와 바람 정보 - 수평 스크롤 */}
            <div className="relative mt-4">
              <div
                style={{
                  width: `${timeSlots.length * 80}px`,
                  minWidth: "320px",
                }}
              >
                {/* 습도 정보 */}
                <div className="mb-3">
                  <div className="flex gap-4.5">
                    {timeSlots.map((slot, index) => (
                      <div
                        key={`humidity-${index}`}
                        className="flex-shrink-0 w-16 text-center"
                      >
                        <div className="text-xs text-blue-600 font-medium">
                          💧{slot.humidity}%
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 평균 온도 및 날씨 요약 */}
      <div className="mt-4 space-y-1">
        <div className="text-center">
          <div className="inline-flex items-center gap-2 rounded-full px-4 py-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: lineColor }}
            />
            <span className="text-sm font-medium text-gray-700">
              평균 {avgTemp.toFixed(1)}°C
            </span>
            <span className="text-xs text-gray-500">
              ({getTemperatureLabel(avgTemp)})
            </span>
          </div>
        </div>

        {/* 바람 정보 요약 */}
        <div className="flex justify-center">
          <div className="px-3 py-2">
            <div className="flex items-center gap-4 text-xs text-gray-600">
              <span className="flex items-center gap-1">
                🌪️ 바람:{" "}
                {getWindDirection(
                  timeSlots[0]?.windU || 0,
                  timeSlots[0]?.windV || 0
                )}
              </span>
              <span className="flex items-center gap-1">
                💧 습도:{" "}
                {Math.round(
                  timeSlots.reduce((sum, slot) => sum + slot.humidity, 0) /
                    timeSlots.length
                )}
                %
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 스크롤바 숨김을 위한 CSS */}
      <style jsx>{`
        .scrollbar-hide {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
      `}</style>
    </div>
  );
}
