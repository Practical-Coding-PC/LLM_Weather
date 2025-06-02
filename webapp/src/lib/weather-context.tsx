"use client";

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";

interface WeatherContextType {
  currentTemp: number;
  setCurrentTemp: (temp: number) => void;
  location: string;
  setLocation: (location: string) => void;
  userId: number;
  setUserId: (userId: number) => void;
}

const WeatherContext = createContext<WeatherContextType | undefined>(undefined);

interface WeatherProviderProps {
  children: ReactNode;
}

// 랜덤한 userId 생성 함수
const generateUserId = (): number => {
  // 6자리 정수 (100000 ~ 999999)
  return Math.floor(100000 + Math.random() * 900000);
};

export const WeatherProvider: React.FC<WeatherProviderProps> = ({
  children,
}) => {
  const [currentTemp, setCurrentTemp] = useState<number>(20); // 기본값 20도
  const [location, setLocation] = useState<string>("현재 위치");
  const [userId, setUserId] = useState<number>();

  // localStorage에서 userId 불러오기 또는 생성하기
  useEffect(() => {
    if (typeof window !== "undefined") {
      let storedUserId = Number(localStorage.getItem("userId"));

      if (!storedUserId) {
        // userId가 없으면 랜덤한 값 생성
        storedUserId = generateUserId();
        localStorage.setItem("userId", storedUserId?.toString());
      }

      setUserId(storedUserId);
    }
  }, []);

  // userId가 변경될 때 localStorage에 저장
  const handleSetUserId = (newUserId: number) => {
    setUserId(newUserId);
    if (typeof window !== "undefined") {
      localStorage.setItem("userId", newUserId.toString());
    }
  };

  return (
    <WeatherContext.Provider
      value={{
        currentTemp,
        setCurrentTemp,
        location,
        setLocation,
        userId: userId || 0,
        setUserId: handleSetUserId,
      }}
    >
      {children}
    </WeatherContext.Provider>
  );
};

export const useWeather = (): WeatherContextType => {
  const context = useContext(WeatherContext);
  if (context === undefined) {
    throw new Error("useWeather must be used within a WeatherProvider");
  }
  return context;
};
