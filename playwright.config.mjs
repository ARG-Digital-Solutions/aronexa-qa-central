import { defineConfig, devices } from '@playwright/test';

const baseURL = process.env.ARONEXA_BASE_URL ?? 'http://127.0.0.1:5175/';
const url = new URL(baseURL);
if (url.protocol !== 'http:' || !['127.0.0.1', 'localhost'].includes(url.hostname)) {
  throw new Error(`Synthetic-only QA refuses a non-local frontend: ${url.origin}`);
}

export default defineConfig({
  testDir: './tests/verified',
  testMatch: '**/*.spec.mjs',
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  forbidOnly: Boolean(process.env.CI),
  outputDir: './artifacts/test-results',
  reporter: [
    ['list'],
    ['html', {outputFolder: './artifacts/playwright-report', open: 'never'}],
    ['junit', {outputFile: './artifacts/results.xml'}]
  ],
  use: {
    baseURL,
    timezoneId: 'Asia/Kolkata',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 10_000,
    launchOptions: { executablePath: process.env.ARONEXA_CHROMIUM_BIN || undefined },
  },
  projects: [
    {name: 'chromium-desktop', use: {...devices['Desktop Chrome'], viewport: {width: 1440, height: 900}}},
  ],
  // Intentionally no webServer: the operator or isolated GitHub CI starts a disposable demo.
  // Never launch the protected Windows database, backend or Docker from this config.
});
