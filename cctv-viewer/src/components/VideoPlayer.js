import React, { useEffect, useRef, useState } from 'react';
import Hls from 'hls.js';

/**
 * VideoPlayer.js
 * - HLS(.m3u8): hls.js 로 재생
 * - MP4 등 네이티브 포맷: video 태그로 재생
 * - 오류 발생 시 메시지 표시
 */

export default function VideoPlayer({ src, width = 640 }) {
  const videoRef = useRef(null);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    if (!src) {
      setErrorMsg('영상 URL이 없습니다.');
      return;
    }

    const video = videoRef.current;
    if (!video) {
      setErrorMsg('비디오 요소를 찾을 수 없습니다.');
      return;
    }

    let hls;

    // HLS.js 로드 및 Media Source Extensions 기반 HLS 스트림 처리
    if (Hls.isSupported()) {
      hls = new Hls();
      hls.on(Hls.Events.ERROR, (_, data) => {
        console.error('HLS 재생 오류:', data);
        setErrorMsg(`HLS 오류: ${data.details || data.type}`);
      });
      hls.loadSource(src);
      hls.attachMedia(video);
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        video.play().catch(err => {
          console.warn('자동 재생 차단:', err);
          setErrorMsg('자동 재생 차단됨. 클릭하여 재생하세요.');
        });
      });
    // Safari 등 네이티브 HLS 지원
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.crossOrigin = 'anonymous';
      video.src = src;
      video.play().catch(err => {
        console.error('네이티브 HLS 오류:', err);
        setErrorMsg('네이티브 HLS 재생 오류');
      });
      
    // MP4/WebM 등 네이티브 포맷
    } else {
      video.crossOrigin = 'anonymous';
      video.src = src;
      video.play().catch(err => {
        console.error('비디오 재생 오류:', err);
        setErrorMsg('비디오 재생 오류');
      });
    }

    return () => {
      // cleanup
      if (hls) {
        hls.destroy();
      }
    };
  }, [src]);

  if (errorMsg) {
    return (
      <div style={{ color: 'red', width: `${width}px`, textAlign: 'center' }}>
        {errorMsg}
      </div>
    );
  }

  return (
    <video
      ref={videoRef}
      controls
      muted
      playsInline
      style={{ width: `${width}px` }}
      preload="metadata"
      crossOrigin="anonymous"
      onClick={() => {
        const v = videoRef.current;
        if (v && v.paused) {
          v.play().catch(console.error);
        }
      }}
    />
  );
}