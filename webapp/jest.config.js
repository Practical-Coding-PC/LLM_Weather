module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jest-environment-jsdom', // Use jsdom for tests that might involve DOM elements or fetch
  roots: ['<rootDir>/src'], // Look for tests in the src directory
  moduleNameMapper: {
    // Handle module aliases (if you have them in tsconfig.json)
    // Example: '^@/components/(.*)$': '<rootDir>/src/components/$1',
    // Adjust according to your project structure if needed for imports like "../lib/utils"
    '^../lib/(.*)$': '<rootDir>/src/lib/$1',
    '^@/lib/(.*)$': '<rootDir>/src/lib/$1', // If using @/lib path
  },
  transform: {
    '^.+\\.(ts|tsx)$': ['ts-jest', {
      tsconfig: 'tsconfig.json',
    }],
  },
  // Automatically clear mock calls and instances between every test
  clearMocks: true,
};
