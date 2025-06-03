import { getTemperatureGradient } from './utils';

describe('getTemperatureGradient', () => {
  it('should return "from-red-50 via-orange-25 to-white" for temperatures >= 30', () => {
    expect(getTemperatureGradient(30)).toBe("from-red-50 via-orange-25 to-white");
    expect(getTemperatureGradient(35)).toBe("from-red-50 via-orange-25 to-white");
  });

  it('should return "from-orange-50 via-yellow-25 to-white" for temperatures >= 25 and < 30', () => {
    expect(getTemperatureGradient(25)).toBe("from-orange-50 via-yellow-25 to-white");
    expect(getTemperatureGradient(29.9)).toBe("from-orange-50 via-yellow-25 to-white");
  });

  it('should return "from-yellow-50 via-green-25 to-white" for temperatures >= 20 and < 25', () => {
    expect(getTemperatureGradient(20)).toBe("from-yellow-50 via-green-25 to-white");
    expect(getTemperatureGradient(24.9)).toBe("from-yellow-50 via-green-25 to-white");
  });

  it('should return "from-green-50 via-blue-25 to-white" for temperatures >= 15 and < 20', () => {
    expect(getTemperatureGradient(15)).toBe("from-green-50 via-blue-25 to-white");
    expect(getTemperatureGradient(19.9)).toBe("from-green-50 via-blue-25 to-white");
  });

  it('should return "from-blue-50 via-indigo-25 to-white" for temperatures >= 10 and < 15', () => {
    expect(getTemperatureGradient(10)).toBe("from-blue-50 via-indigo-25 to-white");
    expect(getTemperatureGradient(14.9)).toBe("from-blue-50 via-indigo-25 to-white");
  });

  it('should return "from-indigo-50 via-purple-25 to-white" for temperatures >= 5 and < 10', () => {
    expect(getTemperatureGradient(5)).toBe("from-indigo-50 via-purple-25 to-white");
    expect(getTemperatureGradient(9.9)).toBe("from-indigo-50 via-purple-25 to-white");
  });

  it('should return "from-purple-50 via-blue-25 to-white" for temperatures < 5', () => {
    expect(getTemperatureGradient(4.9)).toBe("from-purple-50 via-blue-25 to-white");
    expect(getTemperatureGradient(0)).toBe("from-purple-50 via-blue-25 to-white");
    expect(getTemperatureGradient(-5)).toBe("from-purple-50 via-blue-25 to-white");
  });
});
