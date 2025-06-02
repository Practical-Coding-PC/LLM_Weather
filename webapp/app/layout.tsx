import type { Metadata } from "next";
import "./globals.css";
import { WeatherProvider } from "../src/lib/weather-context";

export const metadata: Metadata = {
  title: "날씨 앱",
  description: "날씨 앱",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body className={`antialiased`}>
        <WeatherProvider>{children}</WeatherProvider>
      </body>
    </html>
  );
}
