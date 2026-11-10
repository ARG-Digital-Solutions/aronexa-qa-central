import { defineConfig, devices } from '@playwright/test';
const origin = new URL(process.env.ARONEXA_BASE_URL ?? 'http://127.0.0.1:5175/');
if (origin.protocol !== 'http:' || !['127.0.0.1', 'localhost'].includes(origin.hostname)) {
  throw new Error('COMM-V1 independent QA only allows local HTTP preview');
}
export default defineConfig({
  testDir: './tests/commercial',
  testMatch: '**/*.spec.mjs',
  timeout: 45_000,
  expect: { timeout: 8000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  forbidOnly: !!process.env.CI,
  outputDir: './artifacts/commercial/test-results',
  reporter: [
    ['list'],
    ['junit', { outputFile: './artifacts/commercial/results.xml' }],
    ['html', { outputFolder: './artifacts/commercial/playwright-report', open: 'never' }]
  ],
  use: {
    baseURL: origin.href,
    timezoneId: 'Asia/Kolkata',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    actionTimeout: 8000
  },
  projects: [{ name: 'chromium-desktop', use: { ...devices['Desktop Chrome'], viewport: {width: 1280, height: 900} } }]
});
