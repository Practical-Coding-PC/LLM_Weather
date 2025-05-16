import React from "react";
import { WeatherHeader } from "../components/weather-header";
import { HourlyForecast } from "../components/hourly-forecast";
import { NavigationButtons } from "../components/navigation-buttons";
import { WeatherNewsContainer } from "./weather-news-container";
import { ChatAssistant } from "../components/chat-assistant";

export function WeatherDashboard() {
  const weatherData = {
    location: "춘천",
    currentTemp: "10°C",
    highTemp: "16°C",
    lowTemp: "8°C",
    weatherMessage: "어제보다 바람이\n많이 불고 비가 와요.",
    timeSlots: [
      { time: "1시" },
      { time: "1시" },
      { time: "1시" },
      { time: "1시" },
      { time: "1시" },
      { time: "1시" },
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
