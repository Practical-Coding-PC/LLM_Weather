import React, { useEffect, useState } from 'react';

function App() {
  const [forecast, setForecast] = useState([]);

  useEffect(() => {
    const today = new Date();
    const baseDate = today.toISOString().slice(0, 10).replace(/-/g, '');
    const baseTime = '1030';
    const nx = 60;
    const ny = 127;
  
    const serviceKey = encodeURIComponent(process.env.REACT_APP_WEATHER_KEY);
    const url = `https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtFcst?serviceKey=${serviceKey}&numOfRows=100&pageNo=1&dataType=JSON&base_date=${baseDate}&base_time=${baseTime}&nx=${nx}&ny=${ny}`;
  
    fetch(url)
      .then(res => res.json())
      .then(data => {
        console.log('기상청 응답:', data);
        setForecast(data.response.body.items.item);
      })
      .catch(err => console.error('오류 발생:', err));
  }, []);

  return (
    <div style={{ padding: '2rem' }}>
      <h1>🌤 초단기 기상 예보</h1>
      <ul style={{
          listStyle: 'disc inside',
          padding: 0,
          margin: 0,
          columnCount: 2,
          columnGap: '20px'
        }}>
        {forecast.map((item, idx) => (
          <li key={idx} style={{ marginBottom: '6px', lineHeight: 1.4 }}>
            {item.fcstTime} - {item.category}: {item.fcstValue}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;