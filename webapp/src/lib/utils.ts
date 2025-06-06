// 기온에 따른 배경 그라데이션 색상
export const getTemperatureGradient = (temp: number): string => {
  if (temp >= 30) return "from-red-50/70 via-orange-25/70 to-white";
  if (temp >= 25) return "from-orange-50/70 via-yellow-25/70 to-white";
  if (temp >= 20) return "from-yellow-50/70 via-green-25/70 to-white";
  if (temp >= 15) return "from-green-50/70 via-blue-25/70 to-white";
  if (temp >= 10) return "from-blue-50/70 via-indigo-25/70 to-white";
  if (temp >= 5) return "from-indigo-50/70 via-purple-25/70 to-white";
  return "from-purple-50/70 via-blue-25/70 to-white";
};

export const cn = (...classes: (string | boolean | undefined)[]) => {
  return classes.filter(Boolean).join(" ");
};
