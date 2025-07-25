import React from "react";

// TimeSlot interface to describe weather info needed for indices
interface TimeSlot {
  time: string;
  temp: number;
  sky: number;
  pty: number;
  windU: number;
  windV: number;
  humidity: number;
}

interface WeatherIndicesProps {
  slot: TimeSlot;
}

const calculateLaundryIndex = (slot: TimeSlot): number => {
  // Basic dryness calculation: lower humidity and no precipitation => higher index
  const windSpeed = Math.sqrt(slot.windU ** 2 + slot.windV ** 2);
  let index = 100 - slot.humidity;
  if (slot.pty > 0) index -= 40; // raining reduces drying ability
  if (windSpeed > 3) index += 10; // windy helps drying
  return Math.max(0, Math.min(100, Math.round(index)));
};

const calculateSunscreenIndex = (slot: TimeSlot): number => {
  // Estimate UV exposure using sky condition and temperature
  const hour = (() => {
    const h = parseInt(slot.time.split(" ")[0], 10);
    const isPM = slot.time.includes("PM");
    return isPM && h !== 12 ? h + 12 : h === 12 && !isPM ? 0 : h;
  })();
  const isDaytime = hour >= 10 && hour <= 16;
  let index = slot.sky === 1 && slot.pty === 0 ? 80 : slot.sky === 3 ? 60 : 40;
  if (isDaytime) index += 10;
  if (slot.temp >= 25) index += 10;
  return Math.max(0, Math.min(100, Math.round(index)));
};

const calculateCarwashIndex = (slot: TimeSlot): number => {
  // Car wash index: no precipitation, low humidity, clear sky
  const windSpeed = Math.sqrt(slot.windU ** 2 + slot.windV ** 2);
  let index = 70; // base value

  if (slot.pty > 0) index -= 50; // rain makes car wash pointless
  if (slot.sky === 1) index += 20; // clear sky is best
  else if (slot.sky === 3) index += 10; // partly cloudy is okay

  if (slot.humidity < 60) index += 15; // low humidity helps drying
  else if (slot.humidity > 80) index -= 10;

  if (windSpeed > 5) index -= 10; // too windy can be problematic
  else if (windSpeed > 2) index += 5; // light wind helps drying

  if (slot.temp >= 15 && slot.temp <= 25) index += 10; // ideal temperature range

  return Math.max(0, Math.min(100, Math.round(index)));
};

const calculateOutdoorIndex = (slot: TimeSlot): number => {
  // Outdoor activity index: good temperature, no precipitation, not too windy
  const windSpeed = Math.sqrt(slot.windU ** 2 + slot.windV ** 2);
  let index = 60; // base value

  if (slot.pty > 0) index -= 30; // rain reduces outdoor activities

  // Temperature comfort zone
  if (slot.temp >= 18 && slot.temp <= 25) index += 25; // ideal range
  else if (slot.temp >= 10 && slot.temp <= 30) index += 15; // good range
  else if (slot.temp >= 5 && slot.temp <= 35) index += 5; // acceptable range
  else index -= 20; // too hot or cold

  if (slot.sky === 1) index += 15; // clear sky is great
  else if (slot.sky === 3) index += 5; // partly cloudy is fine

  if (windSpeed > 8) index -= 15; // too windy
  else if (windSpeed > 5) index -= 5; // moderately windy

  if (slot.humidity > 80) index -= 10; // too humid

  return Math.max(0, Math.min(100, Math.round(index)));
};

const getIndexInfo = (
  value: number,
  type: "laundry" | "sunscreen" | "carwash" | "outdoor"
) => {
  if (type === "laundry") {
    if (value >= 80)
      return {
        label: "매우 좋음",
        color: "from-blue-400 to-blue-600",
        bgColor: "bg-blue-50",
        textColor: "text-blue-800",
        icon: "👕",
      };
    if (value >= 60)
      return {
        label: "좋음",
        color: "from-green-400 to-green-600",
        bgColor: "bg-green-50",
        textColor: "text-green-800",
        icon: "👕",
      };
    if (value >= 40)
      return {
        label: "보통",
        color: "from-yellow-400 to-yellow-600",
        bgColor: "bg-yellow-50",
        textColor: "text-yellow-800",
        icon: "👕",
      };
    return {
      label: "주의",
      color: "from-red-400 to-red-600",
      bgColor: "bg-red-50",
      textColor: "text-red-800",
      icon: "👕",
    };
  } else if (type === "sunscreen") {
    if (value >= 80)
      return {
        label: "매우 필요",
        color: "from-red-400 to-red-600",
        bgColor: "bg-red-50",
        textColor: "text-red-800",
        icon: "☀️",
      };
    if (value >= 60)
      return {
        label: "필요",
        color: "from-orange-400 to-orange-600",
        bgColor: "bg-orange-50",
        textColor: "text-orange-800",
        icon: "☀️",
      };
    if (value >= 40)
      return {
        label: "보통",
        color: "from-yellow-400 to-yellow-600",
        bgColor: "bg-yellow-50",
        textColor: "text-yellow-800",
        icon: "🌤️",
      };
    return {
      label: "약간",
      color: "from-green-400 to-green-600",
      bgColor: "bg-green-50",
      textColor: "text-green-800",
      icon: "☁️",
    };
  } else if (type === "carwash") {
    if (value >= 80)
      return {
        label: "매우 좋음",
        color: "from-blue-400 to-blue-600",
        bgColor: "bg-blue-50",
        textColor: "text-blue-800",
        icon: "🚗",
      };
    if (value >= 60)
      return {
        label: "좋음",
        color: "from-green-400 to-green-600",
        bgColor: "bg-green-50",
        textColor: "text-green-800",
        icon: "🚗",
      };
    if (value >= 40)
      return {
        label: "보통",
        color: "from-yellow-400 to-yellow-600",
        bgColor: "bg-yellow-50",
        textColor: "text-yellow-800",
        icon: "🚗",
      };
    return {
      label: "주의",
      color: "from-red-400 to-red-600",
      bgColor: "bg-red-50",
      textColor: "text-red-800",
      icon: "🚗",
    };
  } else {
    if (value >= 80)
      return {
        label: "매우 좋음",
        color: "from-green-400 to-green-600",
        bgColor: "bg-green-50",
        textColor: "text-green-800",
        icon: "🌞",
      };
    if (value >= 60)
      return {
        label: "좋음",
        color: "from-yellow-400 to-yellow-600",
        bgColor: "bg-yellow-50",
        textColor: "text-yellow-800",
        icon: "🌞",
      };
    if (value >= 40)
      return {
        label: "보통",
        color: "from-orange-400 to-orange-600",
        bgColor: "bg-orange-50",
        textColor: "text-orange-800",
        icon: "🌞",
      };
    return {
      label: "주의",
      color: "from-red-400 to-red-600",
      bgColor: "bg-red-50",
      textColor: "text-red-800",
      icon: "🌞",
    };
  }
};

const ProgressBar = ({
  value,
  gradient,
}: {
  value: number;
  gradient: string;
}) => (
  <div className="w-full bg-gray-200 rounded-full h-2 mb-3 overflow-hidden">
    <div
      className={`h-full bg-gradient-to-r ${gradient} transition-all duration-500 ease-out rounded-full`}
      style={{ width: `${value}%` }}
    />
  </div>
);

export function WeatherIndices({ slot }: WeatherIndicesProps) {
  const laundry = calculateLaundryIndex(slot);
  const sunscreen = calculateSunscreenIndex(slot);
  const carwash = calculateCarwashIndex(slot);
  const outdoor = calculateOutdoorIndex(slot);

  const laundryInfo = getIndexInfo(laundry, "laundry");
  const sunscreenInfo = getIndexInfo(sunscreen, "sunscreen");
  const carwashInfo = getIndexInfo(carwash, "carwash");
  const outdoorInfo = getIndexInfo(outdoor, "outdoor");

  return (
    <div className="grid grid-cols-2 gap-4 px-6 mb-6">
      <div
        className={`${laundryInfo.bgColor} backdrop-blur border border-gray-200 rounded-xl p-5 transition-all duration-300 hover:shadow-lg hover:scale-105`}
      >
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="text-2xl">{laundryInfo.icon}</span>
            <span className="text-sm font-semibold text-gray-700">
              빨래 지수
            </span>
          </div>
          <div
            className={`px-2 py-1 rounded-full text-xs font-medium ${laundryInfo.bgColor} ${laundryInfo.textColor}`}
          >
            {laundryInfo.label}
          </div>
        </div>

        <ProgressBar value={laundry} gradient={laundryInfo.color} />

        <div className="flex items-center justify-between">
          <div className={`text-2xl font-bold ${laundryInfo.textColor}`}>
            {laundry}
          </div>
          <div className="text-right">
            <div className="text-xs text-gray-600">습도 {slot.humidity}%</div>
            <div className="text-xs text-gray-600">
              {slot.pty > 0 ? "강수 있음" : "맑음"}
            </div>
          </div>
        </div>
      </div>

      <div
        className={`${sunscreenInfo.bgColor} backdrop-blur border border-gray-200 rounded-xl p-5 transition-all duration-300 hover:shadow-lg hover:scale-105`}
      >
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="text-2xl">{sunscreenInfo.icon}</span>
            <span className="text-sm font-semibold text-gray-700">
              선크림 지수
            </span>
          </div>
          <div
            className={`px-2 py-1 rounded-full text-xs font-medium ${sunscreenInfo.bgColor} ${sunscreenInfo.textColor}`}
          >
            {sunscreenInfo.label}
          </div>
        </div>

        <ProgressBar value={sunscreen} gradient={sunscreenInfo.color} />

        <div className="flex items-center justify-between">
          <div className={`text-2xl font-bold ${sunscreenInfo.textColor}`}>
            {sunscreen}
          </div>
          <div className="text-right">
            <div className="text-xs text-gray-600">온도 {slot.temp}°C</div>
            <div className="text-xs text-gray-600">
              {slot.sky === 1 ? "맑음" : slot.sky === 3 ? "구름많음" : "흐림"}
            </div>
          </div>
        </div>
      </div>

      <div
        className={`${carwashInfo.bgColor} backdrop-blur border border-gray-200 rounded-xl p-5 transition-all duration-300 hover:shadow-lg hover:scale-105`}
      >
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="text-2xl">{carwashInfo.icon}</span>
            <span className="text-sm font-semibold text-gray-700">
              세차 지수
            </span>
          </div>
          <div
            className={`px-2 py-1 rounded-full text-xs font-medium ${carwashInfo.bgColor} ${carwashInfo.textColor}`}
          >
            {carwashInfo.label}
          </div>
        </div>

        <ProgressBar value={carwash} gradient={carwashInfo.color} />

        <div className="flex items-center justify-between">
          <div className={`text-2xl font-bold ${carwashInfo.textColor}`}>
            {carwash}
          </div>
          <div className="text-right">
            <div className="text-xs text-gray-600">습도 {slot.humidity}%</div>
            <div className="text-xs text-gray-600">
              {slot.pty > 0 ? "강수 있음" : "맑음"}
            </div>
          </div>
        </div>
      </div>

      <div
        className={`${outdoorInfo.bgColor} backdrop-blur border border-gray-200 rounded-xl p-5 transition-all duration-300 hover:shadow-lg hover:scale-105`}
      >
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="text-2xl">{outdoorInfo.icon}</span>
            <span className="text-sm font-semibold text-gray-700">
              야외 활동 지수
            </span>
          </div>
          <div
            className={`px-2 py-1 rounded-full text-xs font-medium ${outdoorInfo.bgColor} ${outdoorInfo.textColor}`}
          >
            {outdoorInfo.label}
          </div>
        </div>

        <ProgressBar value={outdoor} gradient={outdoorInfo.color} />

        <div className="flex items-center justify-between">
          <div className={`text-2xl font-bold ${outdoorInfo.textColor}`}>
            {outdoor}
          </div>
          <div className="text-right">
            <div className="text-xs text-gray-600">온도 {slot.temp}°C</div>
            <div className="text-xs text-gray-600">
              {slot.sky === 1 ? "맑음" : slot.sky === 3 ? "구름많음" : "흐림"}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
