import { defineConfig, devices } from '@playwright/test';

const baseURL = process.env.ARONEXA_BASE_URL || 'http://127.0.0.1:5173/';
const parsed = new URL(baseURL);
if (!['localhost', '127.0.0.1'].includes(parsed.hostname)) {
  throw new Error('AroNexa synthetic QA suite only permits localhost/127.0.0.1 targets.');
}

export default defineConfig({
  testDir: './tests',
  testMatch: '**/*.spec.mjs',
  timeout: 35_000,
  expect: { timeout: 7_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  forbidOnly: true,
  outputDir: './artifacts/test-results',
  reporter: [
    ['list'],
    ['html', { outputFolder: './artifacts/playwright-report', open: 'never' }],
    ['junit', { outputFile: './artifacts/results.xml' }]
  ],
  use: {
    baseURL,
    timezoneId: 'Asia/Kolkata',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 10_000
  },
  projects: [
    { name: 'chromium-desktop', use: { ...devices['Desktop Chrome'], viewport: { width: 1280, height: 800 } } },
    { name: 'chromium-tablet', use: { browserName: 'chromium', viewport: { width: 768, height: 1024 }, hasTouch: true } },
    { name: 'chromium-mobile', use: { browserName: 'chromium', viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true } }
  ]
  // Deliberately no webServer: start the synthetic frontend separately.
});
