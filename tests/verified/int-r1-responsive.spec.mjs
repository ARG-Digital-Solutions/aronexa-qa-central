import { test, expect } from '@playwright/test';

/**
 * AroNexa P01-T07-INT-R1 — isolated frontend responsive/navigation acceptance.
 * QA-only, read-only: no patient submission, API writes, Docker or database access.
 * Target the synthetic Vite frontend, e.g. ARONEXA_BASE_URL=http://127.0.0.1:5175/
 */
const baseURL = process.env.ARONEXA_BASE_URL ?? 'http://127.0.0.1:5175/';
const target = new URL(baseURL);
if (!['127.0.0.1', 'localhost', '[::1]'].includes(target.hostname) || target.protocol !== 'http:') {
  throw new Error(`INT-R1 only permits a local HTTP frontend; refusing ${target.origin}`);
}

const viewports = [
  { name: 'desktop-1440', width: 1440, height: 900 },
  { name: 'tablet-768', width: 768, height: 1024 },
  { name: 'mobile-390', width: 390, height: 844 },
  { name: 'small-mobile-320', width: 320, height: 568 },
];

const routes = [
  { name: /Overview/i, heading: 'Good morning, Reception', marker: null },
  { name: /Register patient/i, heading: 'New patient registration', marker: '#fullName' },
  { name: /Patient list/i, heading: 'Patient list', marker: '#search' },
  { name: /Appointments\s*\/\s*check-in/i, heading: 'Appointments and check-in', marker: '#apt-patient' },
];

async function assertNoPageOverflow(page, viewportName, section) {
  const metrics = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
    viewportWidth: window.innerWidth,
  }));
  expect(
    metrics.scrollWidth - metrics.clientWidth,
    `${viewportName}: ${section} has unwanted document-level horizontal scrolling: ${JSON.stringify(metrics)}`,
  ).toBeLessThanOrEqual(3);
}

for (const viewport of viewports) {
  test(`INT-R1 responsive + four-screen navigation | ${viewport.name}`, async ({ page }, testInfo) => {
    test.setTimeout(60_000);
    await page.setViewportSize({ width: viewport.width, height: viewport.height });

    const pageErrors = [];
    page.on('pageerror', err => pageErrors.push(err.message));

    const response = await page.goto(baseURL, { waitUntil: 'domcontentloaded', timeout: 15_000 });
    expect(response?.ok(), 'The isolated synthetic frontend must be reachable').toBe(true);
    await expect(page.getByText('DEMO MODE', { exact: true })).toBeVisible();
    const nav = page.getByRole('navigation', { name: 'Reception navigation' });
    await expect(nav).toBeVisible();

    for (const route of routes) {
      const button = nav.getByRole('button', { name: route.name });
      await expect(button).toBeVisible();
      await button.click();
      await expect(page.getByRole('heading', { level: 1, name: route.heading })).toBeVisible();
      await expect(button).toHaveAttribute('aria-current', 'page');
      if (route.marker) await expect(page.locator(route.marker)).toBeVisible();
      await assertNoPageOverflow(page, viewport.name, route.heading);

      if (route.heading === 'Good morning, Reception' || route.heading === 'Appointments and check-in') {
        const png = await page.screenshot({ fullPage: true });
        await testInfo.attach(`${viewport.name}-${route.heading.toLowerCase().replace(/[^a-z]+/g, '-')}`, {
          body: png,
          contentType: 'image/png',
        });
      }
    }

    expect(pageErrors, `Uncaught browser errors on ${viewport.name}`).toEqual([]);
  });
}
