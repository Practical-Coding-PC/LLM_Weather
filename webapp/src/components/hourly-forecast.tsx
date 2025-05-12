import React from "react";

type TimeSlot = {
  time: string;
};

type HourlyForecastProps = {
  timeSlots: TimeSlot[];
};

export function HourlyForecast({ timeSlots }: HourlyForecastProps) {
  return (
    <div className="border border-gray-400 rounded mb-4">
      <div className="border-b border-gray-400 p-2">
        <div className="flex justify-between">
          <div>시간</div>
          {timeSlots.map((slot, index) => (
            <div key={index}>{slot.time}</div>
          ))}
        </div>
      </div>
      <div className="h-32"></div>
    </div>
  );
}
