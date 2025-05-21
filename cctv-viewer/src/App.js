import React, { useEffect, useState, useRef } from 'react';
import './App.css';
import VideoPlayer from './components/VideoPlayer';
import { fetchCctvList } from './Api';

// 대한민국 지도 컴포넌트 (단순화된 SVG 지도)
const KoreaMap = ({ cctvs, onClickCctv }) => {
  const mapRef = useRef(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // 줌 인/아웃 핸들러 - 확대 범위 확장
  const handleZoom = (direction) => {
    setZoom(prev => {
      const newZoom = direction === 'in' ? prev * 1.3 : prev / 1.3;
      return Math.max(0.5, Math.min(15, newZoom)); // 최대 확대를 8배로 증가, 최소는 0.5배
    });
  };

  // 휠 이벤트 핸들러
  const handleWheel = (e) => {
    e.preventDefault();
    handleZoom(e.deltaY < 0 ? 'in' : 'out');
  };

  // 드래그 시작 핸들러
  const handleMouseDown = (e) => {
    if (e.button !== 0) return; // 왼쪽 버튼만 처리
    setIsDragging(true);
    setDragStart({ x: e.clientX, y: e.clientY });
  };

  // 드래그 중 핸들러
  const handleMouseMove = (e) => {
    if (!isDragging) return;
    
    const dx = e.clientX - dragStart.x;
    const dy = e.clientY - dragStart.y;
    
    setPan(prev => ({ x: prev.x + dx, y: prev.y + dy }));
    setDragStart({ x: e.clientX, y: e.clientY });
  };

  // 드래그 종료 핸들러
  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // 휠 이벤트 리스너 등록
  useEffect(() => {
    const mapElement = mapRef.current;
    if (mapElement) {
      mapElement.addEventListener('wheel', handleWheel, { passive: false });
      
      return () => {
        mapElement.removeEventListener('wheel', handleWheel);
      };
    }
  }, []);

  return (
    <div 
      className="map-container"
      ref={mapRef}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
    >
      <div className="map-controls">
        <button onClick={() => handleZoom('in')}>+</button>
        <button onClick={() => handleZoom('out')}>-</button>
        <button onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }); }}>초기화</button>
      </div>
      
      <svg
        viewBox="0 0 300 400"
        width="100%"
        height="100%"
        style={{ 
          background: '#e6f2ff',
          transform: `scale(${zoom}) translate(${pan.x}px, ${pan.y}px)`,
          transformOrigin: 'center',
          transition: isDragging ? 'none' : 'transform 0.2s ease-out'
        }}
      >
        {/* 대한민국 지도 외곽선 - 조금 더 실제에 가까운 모양 */}
        <path
          d="M80,160 
             C85,140 90,130 100,120 
             C120,100 135,95 150,95 
             C170,95 190,100 210,110
             C235,120 255,130 265,145
             C275,160 280,180 275,205
             C270,230 265,250 255,265
             C245,280 230,295 210,305
             C190,315 170,320 150,320
             C130,320 110,315 95,305
             C80,295 70,285 65,270
             C60,255 55,240 57,220
             C59,200 65,180 80,160 Z"
          fill="#f0f0f0"
          stroke="#ccc"
          strokeWidth="2"
        />
        
        {/* 주요 섬 추가 - 제주도 */}
        <ellipse
          cx="110"
          cy="335"
          rx="25"
          ry="15"
          fill="#f0f0f0"
          stroke="#ccc"
          strokeWidth="2"
        />
        <text x="110" y="338" textAnchor="middle" fontSize="10" fill="#666">제주도</text>
        
        {/* 주요 도시 마커 */}
        <g>
          <circle cx="95" cy="110" r="4" fill="#3498db" />
          <text x="80" y="100" textAnchor="middle" fontSize="12" fill="#333">서울</text>
          
          <circle cx="40" cy="145" r="3" fill="#3498db" />
          <text x="40" y="135" textAnchor="middle" fontSize="12" fill="#333">인천</text>
          
          <circle cx="230" cy="130" r="3" fill="#3498db" />
          <text x="230" y="120" textAnchor="middle" fontSize="12" fill="#333">강릉</text>
          
          <circle cx="230" cy="280" r="3" fill="#3498db" />
          <text x="230" y="295" textAnchor="middle" fontSize="12" fill="#333">부산</text>
          
          <circle cx="130" cy="200" r="3" fill="#3498db" />
          <text x="130" y="190" textAnchor="middle" fontSize="12" fill="#333">대전</text>
          
          <circle cx="40" cy="260" r="3" fill="#3498db" />
          <text x="40" y="275" textAnchor="middle" fontSize="12" fill="#333">광주</text>
          
          <circle cx="180" cy="250" r="3" fill="#3498db" />
          <text x="180" y="265" textAnchor="middle" fontSize="12" fill="#333">울산</text>
          
          <circle cx="160" cy="220" r="3" fill="#3498db" />
          <text x="160" y="235" textAnchor="middle" fontSize="12" fill="#333">대구</text>
        </g>
        
        {/* CCTV 마커 - 크기 더 작게 조정 */}
        {cctvs.map((cctv, index) => {
          if (!cctv.coordx || !cctv.coordy) return null;
          
          // 지도 디멘전 및 여백 설정
          const mapWidth = 300;
          const mapHeight = 400;
          const paddingX = 60;
          const paddingY = 70;
          
          // 좌표 유효성 검사
          const boundedX = Math.max(124, Math.min(132, cctv.coordx));
          const boundedY = Math.max(33, Math.min(39, cctv.coordy));
          
          // 좌표 맞추기 - 실제 지도에 대한 좌표 변환 개선
          const mapRegions = {
            // 한국 전체 지도 좌표 범위
            map: {
              minLong: 124.5, // 서쪽 끝 경도
              maxLong: 131.9, // 동쪽 끝 경도
              minLat: 33.1,   // 남쪽 끝 위도
              maxLat: 38.7    // 북쪽 끝 위도
            },
            // 지역별 중심 좌표
            centers: {
              seoul: { long: 126.98, lat: 37.56 },     // 서울
              incheon: { long: 126.70, lat: 37.45 },  // 인천
              daejeon: { long: 127.38, lat: 36.35 },  // 대전
              daegu: { long: 128.60, lat: 35.87 },    // 대구
              busan: { long: 129.07, lat: 35.18 },    // 부산
              gwangju: { long: 126.85, lat: 35.16 },  // 광주
              gangneung: { long: 128.88, lat: 37.75 }, // 강릉
              jeju: { long: 126.53, lat: 33.50 }      // 제주
            }
          };
          
          // 대한민국 지도에서 지역 위치 파악 기준
          let closestCity = "other";
          let minDistance = Number.MAX_VALUE;
          
          // 가장 가까운 도시 찾기
          Object.entries(mapRegions.centers).forEach(([city, coords]) => {
            const distance = Math.sqrt(
              Math.pow(boundedX - coords.long, 2) + 
              Math.pow(boundedY - coords.lat, 2)
            );
            
            if (distance < minDistance) {
              minDistance = distance;
              closestCity = city;
            }
          });
          
          // 지역별 오프셋 값 초기화
          let offsetX = 0;
          let offsetY = 0;
          
          // SVG 중앙점 기준 좌표를 바탕으로 한국 지도 좌표를 측정
          const svgWidth = mapWidth - (paddingX * 2);
          const svgHeight = mapHeight - (paddingY * 2);
          
          // 실제 경도/위도를 SVG 좌표로 변환 함수
          const longToX = (longitude) => {
            const longRange = mapRegions.map.maxLong - mapRegions.map.minLong;
            // 지도에서의 X 바인딩 좌표 (SVG 공간)
            return paddingX + ((longitude - mapRegions.map.minLong) / longRange) * svgWidth;
          };
          
          const latToY = (latitude) => {
            const latRange = mapRegions.map.maxLat - mapRegions.map.minLat;
            // 지도에서의 Y 바인딩 좌표 (SVG 공간) - 반전되어야 함(위가 위장이미로)
            return paddingY + (1 - (latitude - mapRegions.map.minLat) / latRange) * svgHeight;
          };
          
          // 고유 지역별 추가 오프셋
          if (closestCity === "seoul") {
            offsetX = -5;
            offsetY = -5;
          } else if (closestCity === "busan") {
            offsetX = 5;
            offsetY = 5;  
          } else if (closestCity === "gwangju") {
            offsetX = -10;
            offsetY = 0;
          } else if (closestCity === "gangneung") {
            offsetX = 15;
            offsetY = -5;
          } else if (closestCity === "jeju") {
            offsetX = 0;
            offsetY = 15;
          }
          
          // 마커 중복 방지를 위한 약간의 데이터 견 오프셋 추가
          const jitterX = (index % 5 - 2) * 1.5;
          const jitterY = (Math.floor(index / 5) % 5 - 2) * 1.5;
          
          // 최종 좌표 계산 (SVG 공간)
          const x = longToX(boundedX) + offsetX + jitterX;
          const y = latToY(boundedY) + offsetY + jitterY;
          
          return (
            <g
              key={index}
              onClick={(e) => {
                e.stopPropagation();
                onClickCctv(cctv);
              }}
              style={{ cursor: 'pointer' }}
              className="cctv-marker"
            >
              <circle
                cx={x}
                cy={y}
                r={1}
                fill={closestCity === "seoul" ? "#ffa502" :
                      closestCity === "gangneung" ? "#ff6348" :
                      closestCity === "busan" ? "#1e90ff" :
                      closestCity === "gwangju" ? "#2ed573" :
                      closestCity === "daejeon" ? "#eccc68" :
                      closestCity === "daegu" ? "#a29bfe" :
                      "#ff9f43"}
                stroke="#333"
                strokeWidth="0.5"
              />
            </g>
          );
        })}
      </svg>
    </div>
  );
};

// CCTV 팝업 컴포넌트
const CctvPopup = ({ cctv, onClose }) => {
  if (!cctv) return null;
  
  return (
    <div className="cctv-popup">
      <div className="popup-header">
        <h3>{cctv.cctvname || 'CCTV'}</h3>
        <button onClick={onClose} className="close-button">✕</button>
      </div>
      <div className="popup-content">
        <VideoPlayer src={cctv.cctvurl} width="100%" />
        <div className="popup-info">
          <p>좌표: {cctv.coordx?.toFixed(6) || 'N/A'}, {cctv.coordy?.toFixed(6) || 'N/A'}</p>
          <button className="fullscreen-button" onClick={() => onClose(true)}>
            전체화면으로 보기
          </button>
        </div>
      </div>
    </div>
  );
};

function App() {
  const [cctvs, setCctvs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCctv, setSelectedCctv] = useState(null);
  const [loadAttempt, setLoadAttempt] = useState(0);
  const [viewMode, setViewMode] = useState('map'); // 'map' 또는 'grid'
  const [showPopup, setShowPopup] = useState(false);
  const [popupCctv, setPopupCctv] = useState(null);
  
  // CCTV 데이터 로드
  useEffect(() => {
    loadCctvData();
  }, [loadAttempt]);

  const loadCctvData = () => {
    setLoading(true);
    setError(null);

    fetchCctvList()
      .then(data => {
        console.log("받아온 CCTV 데이터:", data);
        if (!data || data.length === 0) {
          setError("CCTV 데이터를 찾을 수 없습니다.");
        } else {
          setCctvs(data);
        }
      })
      .catch(err => {
        console.error("CCTV 데이터 로딩 오류:", err);
        setError("CCTV 데이터를 불러오는 중 오류가 발생했습니다: " + err.message);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  // 데이터 다시 불러오기
  const handleRefresh = () => {
    setLoadAttempt(prev => prev + 1);
  };

  // CCTV 마커 클릭 핸들러
  const handleClickCctv = (cctv) => {
    setPopupCctv(cctv);
    setShowPopup(true);
  };

  // 팝업 닫기 핸들러
  const handleClosePopup = (goFullscreen = false) => {
    if (goFullscreen) {
      setSelectedCctv(popupCctv);
    }
    setShowPopup(false);
    setPopupCctv(null);
  };

  // 모든 비디오 다시 불러오기
  const handleReloadAllVideos = () => {
    window.location.reload();
  };

  // 전체화면 모드 닫기
  const closeFullscreen = () => {
    setSelectedCctv(null);
  };

  // 전체화면 모드 렌더링
  if (selectedCctv) {
    return (
      <div className="fullscreen-viewer">
        <header className="fullscreen-header">
          <h2>{selectedCctv.cctvname}</h2>
          <button onClick={closeFullscreen} className="close-button">
            닫기 ✕
          </button>
        </header>
        <div className="fullscreen-video">
          <VideoPlayer src={selectedCctv.cctvurl} width="100%" autoPlay={true} />
        </div>
        <div className="fullscreen-info">
          <p>좌표: {selectedCctv.coordx?.toFixed(6)}, {selectedCctv.coordy?.toFixed(6)}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <header>
        <h1>실시간 도로 CCTV</h1>
        <div className="header-buttons">
          <div className="view-toggle">
            <button 
              className={viewMode === 'map' ? 'active' : ''} 
              onClick={() => setViewMode('map')}
            >
              지도 보기
            </button>
            <button 
              className={viewMode === 'grid' ? 'active' : ''} 
              onClick={() => setViewMode('grid')}
            >
              목록 보기
            </button>
          </div>
          <button onClick={handleReloadAllVideos} className="reload-button">
             새로고침
          </button>
        </div>
      </header>

      {loading ? (
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>CCTV 정보를 불러오는 중...</p>
        </div>
      ) : error ? (
        <div className="error">
          <p>{error}</p>
        </div>
      ) : (
        <>
          <div className="stats">
            <p>불러온 CCTV 개수: {cctvs.length}개</p>
            <p>마지막 업데이트: {new Date().toLocaleTimeString()}</p>
          </div>
          
          {viewMode === 'map' ? (
            // 지도 뷰
            <div className="map-view">
              <KoreaMap cctvs={cctvs} onClickCctv={handleClickCctv} />
              
              {showPopup && popupCctv && (
                <CctvPopup cctv={popupCctv} onClose={handleClosePopup} />
              )}
            </div>
          ) : (
            // 그리드 뷰 (기존 코드)
            <div className="cctv-grid">
              {cctvs.map((item, index) => (
                <div key={index} className="cctv-item">
                  <h3>{item.cctvname || `CCTV #${index + 1}`}</h3>
                  <VideoPlayer src={item.cctvurl} />
                  <div className="cctv-info">
                    <p>좌표: {item.coordx?.toFixed(6) || 'N/A'}, {item.coordy?.toFixed(6) || 'N/A'}</p>
                    <button 
                      onClick={() => setSelectedCctv(item)}
                      className="fullscreen-button"
                    >
                      전체화면
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
          
          {cctvs.length === 0 && (
            <div className="no-results">
              <p>표시할 CCTV가 없습니다.</p>
            </div>
          )}
        </>
      )}
      
      <footer className="app-footer">
        <p>© 2025 실시간 도로 CCTV 뷰어 | API 제공: <a href="https://its.go.kr" target="_blank" rel="noopener noreferrer">ITS (국가교통정보센터)</a></p>
      </footer>
    </div>
  );
}

export default App;