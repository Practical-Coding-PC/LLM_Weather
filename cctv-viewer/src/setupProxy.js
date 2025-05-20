const { createProxyMiddleware, responseInterceptor } = require('http-proxy-middleware');
const url = require('url');

module.exports = function(app) {
  // ITS API 프록시
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'https://openapi.its.go.kr:9443',
      changeOrigin: true,
      pathRewrite: {
        '^/api': '',
      },
      onProxyReq: (proxyReq, req, res) => {
        // 원본 헤더 추가 (필요한 경우)
        proxyReq.setHeader('Origin', 'http://localhost:3000');
      },
      onError: (err, req, res) => {
        console.error('API Proxy error:', err);
        res.status(500).send('API Proxy error');
      },
    })
  );

  // HLS 스트림 프록시
  app.use(
    '/hls',
    createProxyMiddleware({
      target: 'http://cctvsec.ktict.co.kr',
      changeOrigin: true,
      selfHandleResponse: true,
      pathRewrite: (path, req) => {
        const originalUrl = url.parse(req.url, true).query.url || '';
        return originalUrl.replace(/^https?:\/\/[^/]+/, '');
      },
      onProxyRes: responseInterceptor(async (responseBuffer, proxyRes, req, res) => {
        // 디버깅 정보 추가
        console.log('Proxy response received:', {
          url: req.url,
          contentType: proxyRes.headers['content-type'],
          status: proxyRes.statusCode,
          length: responseBuffer.length
        });

        // 버퍼를 문자열로 변환
        let body = responseBuffer.toString('utf8');
        const contentType = (proxyRes.headers['content-type'] || '').toLowerCase();

        // m3u8 플레이리스트인 경우 TS 세그먼트 URI 다시 작성
        if (contentType.includes('mpegurl') || req.url.includes('.m3u8')) {
          console.log('Rewriting m3u8 playlist');
          
          // 콘텐츠 확인
          console.log('Original m3u8 content:', body.slice(0, 500));
          
          body = body.replace(
            /^(?!#)(.+\.ts.*)$/gm,
            (line) => {
              const segmentPath = line.trim();
              // 절대 URL 구성
              const absoluteUrl = `http://cctvsec.ktict.co.kr${segmentPath.startsWith('/') ? '' : '/'}${segmentPath}`;
              const proxyUrl = `/hls?url=${encodeURIComponent(absoluteUrl)}`;
              console.log(`Rewriting segment: ${segmentPath} -> ${proxyUrl}`);
              return proxyUrl;
            }
          );
          
          // 콘텐츠 타입 설정
          res.setHeader('content-type', 'application/vnd.apple.mpegurl');
          res.setHeader('access-control-allow-origin', '*');
        } else if (req.url.includes('.ts')) {
          // TS 파일은 바이너리 데이터이므로 원본 버퍼 반환
          console.log('Passing through TS segment');
          return responseBuffer;
        }
        
        return body;
      }),
      onError: (err, req, res) => {
        console.error('HLS Proxy error:', err);
        res.status(500).send('HLS Proxy error');
      },
    })
  );
};