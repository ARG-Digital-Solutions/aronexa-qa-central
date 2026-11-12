import {defineConfig,devices} from '@playwright/test';

// R1-07 opt-in browser UX only; isolated from QA Central's default suite.
const target=process.env.ARONEXA_DOCTOR_BASE_URL;
if(!target)throw Error('Set ARONEXA_DOCTOR_BASE_URL to the local R1-07 connected preview');
const u=new URL(target);
if(u.protocol!=='http:'||!['127.0.0.1','localhost'].includes(u.hostname)
  ||u.pathname!=='/connected-doctor-preview.html')
  throw Error('R1-07 refuses non-local or unrelated Playwright server');
export default defineConfig({
  testDir:'./tests/r1-07',
  testMatch:'**/*.spec.mjs',
  timeout:60_000,
  expect:{timeout:10_000},
  retries:0,
  workers:1,
  fullyParallel:false,
  forbidOnly:Boolean(process.env.CI),
  outputDir:'./artifacts/r1-07-results',
  reporter:[
    ['list'],
    ['junit',{outputFile:'./artifacts/r1-07-results.xml'}],
    ['html',{outputFolder:'./artifacts/r1-07-report',open:'never'}],
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
  // No webServer. Operator starts isolated Vite manually.
});
