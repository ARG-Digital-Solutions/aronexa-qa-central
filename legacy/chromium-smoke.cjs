const { chromium } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch({
    headless: true
  });

  console.log("CHROMIUM_LAUNCH_PASS");
  console.log("Version:", browser.version());

  await browser.close();
})().catch(error => {
  console.error("CHROMIUM_LAUNCH_FAIL");
  console.error(error);
  process.exit(1);
});
