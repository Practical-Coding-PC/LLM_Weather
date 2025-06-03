import { getUltraShortTermWeather, getWeatherNews, WeatherApiItem, WeatherNewsItem } from './weather-api';

// Mocking the global fetch function
global.fetch = jest.fn();

// Helper to create a JSON response
const mockJsonResponse = (data: any, ok = true, status = 200) =>
  Promise.resolve({
    ok,
    status,
    json: () => Promise.resolve(data),
  } as Response);

// Helper to create a fetch error
const mockFetchError = (message: string) => Promise.reject(new Error(message));

describe('Weather API', () => {
  beforeEach(() => {
    // Clear all instances and calls to constructor and all methods on `fetch`
    (fetch as jest.Mock).mockClear();
  });

  // Tests for getUltraShortTermWeather
  describe('getUltraShortTermWeather', () => {
    const mockLatitude = 35.123;
    const mockLongitude = 129.456;
    const mockWeatherData: WeatherApiItem[] = [
      { fcstDate: '20230101', fcstTime: '0600', category: 'T1H', fcstValue: '25' },
      { fcstDate: '20230101', fcstTime: '0600', category: 'SKY', fcstValue: '1' },
    ];

    it('should fetch ultra short term weather data successfully', async () => {
      (fetch as jest.Mock).mockReturnValueOnce(
        mockJsonResponse({ requestCode: '200', items: mockWeatherData })
      );

      const data = await getUltraShortTermWeather(mockLatitude, mockLongitude);
      expect(fetch).toHaveBeenCalledTimes(1);
      expect(fetch).toHaveBeenCalledWith(
        `http://localhost:8000/weather/ultra_short_term?latitude=${mockLatitude}&longitude=${mockLongitude}`
      );
      expect(data).toEqual({ requestCode: '200', items: mockWeatherData });
    });

    it('should throw an error if the fetch fails (network error)', async () => {
      (fetch as jest.Mock).mockReturnValueOnce(mockFetchError('Network failure'));

      await expect(
        getUltraShortTermWeather(mockLatitude, mockLongitude)
      ).rejects.toThrow('Network failure');
      expect(fetch).toHaveBeenCalledTimes(1);
    });

    it('should throw an error if response is not ok (e.g., 500 status)', async () => {
      (fetch as jest.Mock).mockReturnValueOnce(
        mockJsonResponse({ detail: 'Server error' }, false, 500)
      );

      await expect(
        getUltraShortTermWeather(mockLatitude, mockLongitude)
      ).rejects.toThrow('Server error');
      expect(fetch).toHaveBeenCalledTimes(1);
    });

    it('should throw a generic error if response is not ok and error JSON is malformed', async () => {
      (fetch as jest.Mock).mockReturnValueOnce(
        Promise.resolve({
          ok: false,
          status: 500,
          json: () => Promise.reject(new Error("Malformed JSON")), // Simulate JSON parsing error
        } as Response)
      );

      await expect(
        getUltraShortTermWeather(mockLatitude, mockLongitude)
      ).rejects.toThrow('Unknown error while fetching weather data');
      expect(fetch).toHaveBeenCalledTimes(1);
    });
  });

  // Tests for getWeatherNews
  describe('getWeatherNews', () => {
    const mockLatitude = 35.123;
    const mockLongitude = 129.456;
    const mockNewsData: WeatherNewsItem[] = [
      { id: '1', title: 'Heavy Rain Expected', url: 'http://news.example.com/rain', source: 'Example News', publishTime: '2023-01-01T10:00:00Z', summary: 'Heavy rain will fall tomorrow.' },
      { id: '2', title: 'Sunny Skies Ahead', url: 'http://news.example.com/sunny', source: 'Example News', publishTime: '2023-01-01T11:00:00Z', summary: 'Clear skies expected for the weekend.' },
    ];

    it('should fetch weather news successfully', async () => {
      (fetch as jest.Mock).mockReturnValueOnce(
        mockJsonResponse({ news: mockNewsData })
      );

      const data = await getWeatherNews(mockLatitude, mockLongitude);
      expect(fetch).toHaveBeenCalledTimes(1);
      expect(fetch).toHaveBeenCalledWith(
        `http://localhost:8000/weather/news?latitude=${mockLatitude}&longitude=${mockLongitude}`
      );
      expect(data).toEqual({ news: mockNewsData });
    });

    it('should throw an error if the fetch fails (network error)', async () => {
      (fetch as jest.Mock).mockReturnValueOnce(mockFetchError('Network failure'));

      await expect(
        getWeatherNews(mockLatitude, mockLongitude)
      ).rejects.toThrow('Network failure');
      expect(fetch).toHaveBeenCalledTimes(1);
    });

    it('should throw an error if response is not ok (e.g., 404 status)', async () => {
      (fetch as jest.Mock).mockReturnValueOnce(
        mockJsonResponse({ detail: 'Not found' }, false, 404)
      );

      await expect(
        getWeatherNews(mockLatitude, mockLongitude)
      ).rejects.toThrow('Not found');
      expect(fetch).toHaveBeenCalledTimes(1);
    });
    
    it('should throw a generic error if response is not ok and error JSON is malformed', async () => {
      (fetch as jest.Mock).mockReturnValueOnce(
        Promise.resolve({
          ok: false,
          status: 500,
          json: () => Promise.reject(new Error("Malformed JSON")), // Simulate JSON parsing error
        } as Response)
      );

      await expect(
        getWeatherNews(mockLatitude, mockLongitude)
      ).rejects.toThrow('Unknown error while fetching weather news');
      expect(fetch).toHaveBeenCalledTimes(1);
    });
  });
});
