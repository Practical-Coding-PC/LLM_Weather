export async function fetchCctvList() {
  const key = process.env.REACT_APP_CCTV_API_KEY;
  if (!key) {
    throw new Error('환경변수 REACT_APP_CCTV_API_KEY가 설정되지 않았습니다.');
  }

  // 조회할 type 목록
  const types = ['its', 'ex'];

  // 각 type별 API 호출 함수
  const fetchByType = async (type) => {
    const params = new URLSearchParams({
      apiKey:   key,
      type:     'ex',     // 'its' 또는 'ex'
      cctvType: '1',      // 실시간 HLS
      minX:     124.61167,
      maxX:     131.87222,
      minY:     33.11028,
      maxY:     38.61111,
      getType:  'json',   // JSON 응답
    });
    const url = `https://openapi.its.go.kr:9443/cctvInfo?${params.toString()}`;
    const resp = await fetch(url);
    if (!resp.ok) {
      throw new Error(`ITS API 요청 실패(type=${type}): ${resp.status} ${resp.statusText}`);
    }
    const { response: payload } = await resp.json();
    return payload?.data || [];
  };

  // 모든 type 호출 후 병합
  const results = await Promise.all(types.map(fetchByType));
  const allCctvs = results.flat();

  // 모든 CCTV 데이터 리턴 (필터링 제거)
  return allCctvs
    .map(item => ({
      cctvname: item.cctvname.replace(/;$/, ''),
      cctvurl:  item.cctvurl.replace(/;$/, ''),
      coordx:   parseFloat(item.coordx) || 0,
      coordy:   parseFloat(item.coordy) || 0,
    }));
}