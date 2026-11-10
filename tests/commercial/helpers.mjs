import { expect } from '@playwright/test';
const base = new URL(process.env.ARONEXA_BASE_URL ?? 'http://127.0.0.1:5175/');
if (base.protocol !== 'http:' || !['127.0.0.1', 'localhost'].includes(base.hostname)) {
  throw new Error('No external application hosts in synthetic QA');
}
export async function openLocalPreview(page, filename) {
  await page.route('**/*', async route => {
    const request = route.request();
    const target = new URL(request.url());
    if (target.origin !== base.origin || !['GET','HEAD'].includes(request.method())) {
      await route.abort('blockedbyclient');
    } else {
      await route.continue();
    }
  });
  const response = await page.goto(new URL(filename, base).href, { waitUntil:'domcontentloaded' });
  expect(response?.ok(), 'Preview must respond successfully from local Vite').toBe(true);
}
export async function noHorizontalScroll(page) {
  const width = await page.evaluate(() => ({
    scroll: document.documentElement.scrollWidth,
    viewport: document.documentElement.clientWidth
  }));
  expect(width.scroll - width.viewport).toBeLessThanOrEqual(4);
}
