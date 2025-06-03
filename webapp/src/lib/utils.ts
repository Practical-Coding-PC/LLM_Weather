// 기온에 따른 배경 그라데이션 색상
export const getTemperatureGradient = (temp: number): string => {
  if (temp >= 30) return "from-red-50 via-orange-25 to-white";
  if (temp >= 25) return "from-orange-50 via-yellow-25 to-white";
  if (temp >= 20) return "from-yellow-50 via-green-25 to-white";
  if (temp >= 15) return "from-green-50 via-blue-25 to-white";
  if (temp >= 10) return "from-blue-50 via-indigo-25 to-white";
  if (temp >= 5) return "from-indigo-50 via-purple-25 to-white";
  return "from-purple-50 via-blue-25 to-white";
};
