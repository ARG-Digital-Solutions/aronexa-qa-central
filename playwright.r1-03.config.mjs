import {defineConfig,devices} from '@playwright/test';

/** Explicitly opt-in only, so default verified synthetic QA stays unchanged. */
const target=process.env.ARONEXA_CONNECTED_BASE_URL;
if(!target)throw new Error('Set ARONEXA_CONNECTED_BASE_URL to the local connected preview');
const u=new URL(target);
if(u.protocol!=='http:' || !['localhost','127.0.0.1'].includes(u.hostname)
  || u.pathname!=='/connected-reception-preview.html'){
  throw new Error('Refusing non-local/non-preview R1-03 browser QA target');
}
export default defineConfig({
  testDir:'./tests/r1-03',
  testMatch:'**/*.spec.mjs',
  timeout:60_000,
  expect:{timeout:10_000},
  retries:0,
  workers:1,
  fullyParallel:false,
  forbidOnly:Boolean(process.env.CI),
  outputDir:'./artifacts/r1-03-test-results',
  reporter:[
    ['list'],
    ['html',{outputFolder:'./artifacts/r1-03-playwright-report',open:'never'}],
    ['junit',{outputFile:'./artifacts/r1-03-results.xml'}],
  ],
  use:{
    baseURL:target,
    timezoneId:'Asia/Kolkata',
    screenshot:'only-on-failure',
    trace:'retain-on-failure',
    video:'retain-on-failure',
    actionTimeout:10_000,
    launchOptions:{executablePath:process.env.ARONEXA_CHROMIUM_BIN||undefined},
  },
  projects:[{
    name:'chromium-desktop',
    use:{...devices['Desktop Chrome'],viewport:{width:1440,height:900}},
  }],
  // Deliberately no webServer; operator must start Vite locally.
});
