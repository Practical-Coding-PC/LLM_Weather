import React, { useEffect, useState } from 'react';
import { fetchCctvWeather } from './Api';

function App() {
  const [weather, setWeather] = useState([]);

  useEffect(() => {
    fetchCctvWeather('0500C00006', '02')  // ← 01로 테스트!
      .then(data => {
        console.log("받아온 날씨 데이터:", data);
        setWeather(data);
      })
      .catch(console.error);
  }, []);

  return (
    <div>
      <h1>CCTV 도로날씨 정보</h1>
      {weather.length === 0 ? (
        <p>불러오는 중...</p>
      ) : (
        <ul>
          {weather.map((item, index) => (
            <li key={index}>
              수집시간: {item.baseDate} {item.baseTime} / 날씨: {item.weatherNm}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default App;