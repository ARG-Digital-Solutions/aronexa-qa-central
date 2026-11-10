import {defineConfig,devices} from '@playwright/test';
const feature=process.env.ARONEXA_QA_FEATURE;
if(!['consultation','smart-rx','billing'].includes(feature))throw Error('Unapproved feature');
const url=new URL(process.env.ARONEXA_BASE_URL??'http://127.0.0.1:5175/');
if(url.protocol!=='http:'||!['localhost','127.0.0.1'].includes(url.hostname))throw Error('Only localhost');
export default defineConfig({
  testDir:'./tests/commercial',testMatch:feature+'.spec.mjs',
  forbidOnly:!!process.env.CI,workers:1,retries:0,
  outputDir:'./artifacts/commercial/test-results',
  reporter:[['list'],['junit',{outputFile:'./artifacts/commercial/junit.xml'}],['html',{outputFolder:'./artifacts/commercial/report',open:'never'}]],
  use:{baseURL:url.href,trace:'retain-on-failure',screenshot:'only-on-failure',video:'retain-on-failure'},
  projects:[{name:'chromium-desktop',use:{...devices['Desktop Chrome']}}]
});
