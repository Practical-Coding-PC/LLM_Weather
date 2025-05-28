import React from "react";
import { LineChart, Line, ResponsiveContainer } from "recharts";

type TimeSlot = {
  time: string;
  temp: number;
};

type HourlyForecastProps = {
  timeSlots: TimeSlot[];
};

export function HourlyForecast({ timeSlots }: HourlyForecastProps) {
  return (
    <div className="border border-gray-400 rounded mb-4">
      <div className="flex justify-between">
        {timeSlots.map((slot) => (
          <div key={slot.time}>{slot.time}</div>
        ))}
      </div>
      <div className="h-24">
        <ResponsiveContainer>
          <LineChart data={timeSlots}>
            <Line type="linear" dataKey="temp" stroke="#8884d8" />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="flex justify-between">
        {timeSlots.map((slot) => (
          <div key={slot.time}>{slot.temp}°C</div>
        ))}
      </div>
    </div>
  );
}
