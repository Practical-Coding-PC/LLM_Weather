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
  userId: number | undefined;
}

const WeatherContext = createContext<WeatherContextType | undefined>(undefined);

interface WeatherProviderProps {
  children: ReactNode;
}

export const WeatherProvider: React.FC<WeatherProviderProps> = ({
  children,
}) => {
  const [currentTemp, setCurrentTemp] = useState<number>(20); // 기본값 20도
  const [location, setLocation] = useState<string>("현재 위치");
  const [userId, setUserId] = useState<number>();

  // localStorage에서 userId 불러오기 또는 생성하기
  useEffect(() => {
    const storedUserId = Number(localStorage.getItem("userId"));

    console.log("fdfdffdfd")
    console.log(storedUserId)
    if (Number.isNaN(storedUserId)) {
      // userId가 없으면 랜덤한 값 생성
      const location = "춘천";

      fetch(`http://localhost:8000/users`, {
        method: "POST",
        body: JSON.stringify({ location }),
        headers: {
          "Content-Type": "application/json",
        },
      })
        .then((res) => res.json() as Promise<{ user_id: number }>)
        .then((data) => {
          setUserId(data.user_id);
        })
        .catch((err) => {
          console.error(err);
        });
        console.log(storedUserId)
      localStorage.setItem("userId", storedUserId?.toString());
    }

    setUserId(storedUserId);
  }, []);

  return (
    <WeatherContext.Provider
      value={{
        currentTemp,
        setCurrentTemp,
        location,
        setLocation,
        userId,
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
