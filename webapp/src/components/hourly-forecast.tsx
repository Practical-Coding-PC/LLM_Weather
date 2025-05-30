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
};

type HourlyForecastProps = {
  timeSlots: TimeSlot[];
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
  payload?: Array<{ value: number }>;
  label?: string;
}) => {
  if (active && payload && payload.length) {
    const temp = payload[0].value;
    const color = getTemperatureColor(temp);
    const tempLabel = getTemperatureLabel(temp);

    return (
      <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200">
        <p className="text-sm font-medium text-gray-600">{label}</p>
        <p className="text-lg font-bold" style={{ color }}>
          {temp}°C
        </p>
        <p className="text-xs text-gray-500">{tempLabel}</p>
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
      {/* 온도 범위 표시 */}
      <div className="flex justify-between items-center mb-4 pt-4">
        <div className="text-sm font-medium text-gray-700">
          시간별 기온 변화
        </div>
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

      {/* 온도 표시 */}
      <div className="flex justify-between mb-3 px-2">
        {timeSlots.map((slot) => (
          <div key={slot.time} className="text-center">
            <div
              className="text-sm font-bold mb-1 drop-shadow-sm"
              style={{ color: getTemperatureColor(slot.temp) }}
            >
              {slot.temp}°
            </div>
            <div className="text-xs text-gray-500 font-medium">
              {getTemperatureLabel(slot.temp)}
            </div>
          </div>
        ))}
      </div>

      {/* 차트 */}
      <div className="h-40 rounded-lg p-2">
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
            <Tooltip content={<CustomTooltip />} />
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

      {/* 평균 온도 표시 */}
      <div className="mt-4 text-center">
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
    </div>
  );
}
