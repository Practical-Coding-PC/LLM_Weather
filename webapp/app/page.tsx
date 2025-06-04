"use client";

import { WeatherDashboard } from "../src/containers/weather-dashboard";
import { useEffect } from "react";

export default function Page() {
  useEffect(() => {
    if ("serviceWorker" in navigator && "PushManager" in window) {
      navigator.serviceWorker.register("/sw.js", {
        scope: "/",
        updateViaCache: "none",
      });
    }
  }, []);

  return <WeatherDashboard />;
}
