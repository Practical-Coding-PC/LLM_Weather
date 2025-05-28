import React from "react";
import { WeatherHeader } from "../components/weather-header";
import { NavigationButtons } from "../components/navigation-buttons";
import { WeatherNewsContainer } from "./weather-news-container";
import { ChatAssistant } from "../components/chat-assistant";
import dynamic from "next/dynamic";

const HourlyForecast = dynamic(
  () =>
    import("../components/hourly-forecast").then((mod) => mod.HourlyForecast),
  {
    ssr: false,
  }
);

export function WeatherDashboard() {
  const weatherData = {
    location: "춘천",
    currentTemp: "10°C",
    highTemp: "16°C",
    lowTemp: "8°C",
    weatherMessage: "어제보다 바람이\n많이 불고 비가 와요.",
    timeSlots: [
      { time: "1시", temp: 10 },
      { time: "2시", temp: 13 },
      { time: "3시", temp: 17 },
      { time: "4시", temp: 24 },
      { time: "5시", temp: 18 },
      { time: "6시", temp: 15 },
    ],
    navButtons: [
      { label: "습도", onClick: () => console.log("습도 clicked") },
      { label: "미세 먼지", onClick: () => console.log("미세 먼지 clicked") },
      { label: "자외선", onClick: () => console.log("자외선 clicked") },
      { label: "바람", onClick: () => console.log("바람 clicked") },
    ],
  };

  return (
    <div className="max-w-md mx-auto h-screen flex flex-col p-4">
      <WeatherHeader
        location={weatherData.location}
        currentTemp={weatherData.currentTemp}
        highTemp={weatherData.highTemp}
        lowTemp={weatherData.lowTemp}
        weatherMessage={weatherData.weatherMessage}
      />

      <HourlyForecast timeSlots={weatherData.timeSlots} />

      <NavigationButtons buttons={weatherData.navButtons} />

      <WeatherNewsContainer location={weatherData.location} />

      <ChatAssistant onClick={() => console.log("Chat assistant clicked")} />
    </div>
  );
}
