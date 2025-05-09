import axios from 'axios';

export const fetchCctvWeather = async (eqmtId = "0500C00122", hhCode = "03") => {
  const SERVICE_KEY = process.env.REACT_APP_PUBLIC_DATA_KEY;

  try {
    const response = await axios.get(
      'http://apis.data.go.kr/1360000/RoadWthrInfoService/getCctvStnRoadWthr',
      {
        params: {
          serviceKey: SERVICE_KEY,
          numOfRows: 10,
          pageNo: 1,
          dataType: 'JSON',
          eqmtId,
          hhCode,
        },
      }
    );

    console.log("응답 전체:", response.data);

    const header = response.data?.response?.header;
    const items = response.data?.response?.body?.items?.item;

    if (!header || header.resultCode !== "00") {
      console.warn("API 응답 오류:", header?.resultMsg || "응답 없음");
      return [];
    }

    if (!items) {
      console.warn("⚠️ 데이터가 존재하지 않음");
      return [];
    }

    return items;
  } catch (error) {
    console.error("API 요청 실패:", error);
    return [];
  }
};