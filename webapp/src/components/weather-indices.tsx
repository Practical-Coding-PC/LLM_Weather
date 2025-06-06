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

const getLabel = (value: number): string => {
  if (value >= 80) return "매우 좋음";
  if (value >= 60) return "좋음";
  if (value >= 40) return "보통";
  return "주의";
};

export function WeatherIndices({ slot }: WeatherIndicesProps) {
  const laundry = calculateLaundryIndex(slot);
  const sunscreen = calculateSunscreenIndex(slot);

  return (
    <div className="flex justify-around gap-4 px-6 mb-4">
      <div className="flex-1 bg-white/40 backdrop-blur border border-gray-200 rounded-lg p-4 text-center">
        <div className="text-sm font-semibold text-gray-700 mb-1">빨래 지수</div>
        <div className="text-xl font-bold text-gray-800">{laundry}</div>
        <div className="text-xs text-gray-600 mt-1">{getLabel(laundry)}</div>
      </div>
      <div className="flex-1 bg-white/40 backdrop-blur border border-gray-200 rounded-lg p-4 text-center">
        <div className="text-sm font-semibold text-gray-700 mb-1">선크림 지수</div>
        <div className="text-xl font-bold text-gray-800">{sunscreen}</div>
        <div className="text-xs text-gray-600 mt-1">{getLabel(sunscreen)}</div>
      </div>
    </div>
  );
}
