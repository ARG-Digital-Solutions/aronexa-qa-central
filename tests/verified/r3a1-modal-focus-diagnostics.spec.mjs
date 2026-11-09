import { test, expect } from '@playwright/test';

/**
 * P01-T07-INT-R3-A1 QA-only focus diagnostics.
 * Does not modify the existing R3A-05 assertion.
 * Frozen application SHA is selected by the central workflow: 52809efbc077cd6abb6860d870cc487cc8eddc42.
 */
const baseURL = process.env.ARONEXA_BASE_URL ?? 'http://127.0.0.1:5175/';
const origin = new URL(baseURL);
if (origin.protocol !== 'http:' || !['localhost', '127.0.0.1', '[::1]'].includes(origin.hostname)) {
  throw new Error('Only local synthetic frontend URLs are permitted.');
}

test('R3A1-DIAG modal focus timeline, forward and backward Tab, no background interactive focus', async ({ page }, testInfo) => {
  await page.route('**/*', route => {
    const request = route.request();
    const requested = new URL(request.url());
    if (requested.origin !== origin.origin || !['GET', 'HEAD'].includes(request.method())) {
      return route.abort('blockedbyclient');
    }
    return route.continue();
  });

  const response = await page.goto(baseURL, { waitUntil: 'domcontentloaded' });
  expect(response?.ok()).toBe(true);
  await expect(page.getByText('DEMO MODE', { exact: true })).toBeVisible();

  await page.getByRole('navigation', { name: 'Reception navigation' })
    .getByRole('button', { name: /Register patient/i }).click();
  await page.locator('#fullName').fill('Synthetic Accessibility QA');
  await page.getByRole('button', { name: 'Review & continue' }).click();
  const dialog = page.getByRole('dialog');
  await expect(dialog).toBeVisible();
  await expect(page.locator('#reviewTitle')).toBeFocused();

  const events = [];
  async function snapshot(key, index) {
    const record = await page.evaluate(() => {
      const modal = document.querySelector('dialog');
      const active = document.activeElement;
      const text = (active?.textContent ?? '').replace(/\s+/g, ' ').trim().slice(0, 90);
      const tag = active?.tagName ?? 'null';
      const id = active?.id ?? '';
      const inside = Boolean(modal && active && modal.contains(active));
      const backgroundInteractive = Boolean(active && !inside &&
        active.matches?.('button,a[href],input,select,textarea,[tabindex]:not([tabindex="-1"])'));
      return {
        activeTag: tag, activeId: id, activeText: text,
        activeIsDocumentBody: active === document.body,
        activeIsDialog: active === modal,
        activeInsideDialog: inside,
        outsideInteractiveFocus: backgroundInteractive,
        dialogOpen: Boolean(modal?.open),
        dialogIsTopLayer: Boolean(modal?.matches(':modal')),
        documentHasFocus: document.hasFocus(),
      };
    });
    const event = { key, index, ...record };
    events.push(event);
    // Structured diagnostic log retained even when the original R3A-05 test fails.
    console.log('R3A1_FOCUS_EVENT=' + JSON.stringify(event));
  }

  await snapshot('initial', 0);
  for (let i = 1; i <= 10; i++) {
    await page.keyboard.press('Tab');
    await snapshot('Tab', i);
  }
  for (let i = 1; i <= 10; i++) {
    await page.keyboard.press('Shift+Tab');
    await snapshot('Shift+Tab', i);
  }

  await testInfo.attach('R3A1-focus-timeline.json', {
    body: Buffer.from(JSON.stringify({
      sourceSha: '52809efbc077cd6abb6860d870cc487cc8eddc42',
      qaTest: 'R3A1-DIAG',
      events,
    }, null, 2)),
    contentType: 'application/json',
  });

  await expect(dialog).toBeVisible();
  expect(events.every(e => e.dialogOpen && e.dialogIsTopLayer),
    'Native modal must remain open and in top layer throughout tab sequence').toBe(true);
  expect(events.filter(e => e.outsideInteractiveFocus),
    'No interactive element behind the native modal may receive focus').toEqual([]);
  expect(events.some(e => e.activeInsideDialog),
    'At least one keyboard step should focus a descendant of the review dialog').toBe(true);
});
