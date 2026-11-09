import { test, expect } from '@playwright/test';

/**
 * P01-T07-INT-R3-A — automated accessibility acceptance for synthetic Reception + Appointments.
 * Ported from the R3-A Windows test kit into the existing central QA runner.
 * Target application: frozen PR #61, SHA 52809efbc077cd6abb6860d870cc487cc8eddc42.
 * Not a replacement for independent NVDA / VoiceOver manual acceptance.
 */
const baseURL = process.env.ARONEXA_BASE_URL ?? 'http://127.0.0.1:5175/';
const target = new URL(baseURL);
if (target.protocol !== 'http:' || !['127.0.0.1', 'localhost', '[::1]'].includes(target.hostname)) {
  throw new Error('R3-A refuses non-local frontend: ' + target.origin);
}
const todayIndia = () => {
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat('en-US', {
      timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit',
    }).formatToParts(new Date()).map(part => [part.type, part.value])
  );
  return parts.year + '-' + parts.month + '-' + parts.day;
};
async function navigate(page, name) {
  await page.getByRole('navigation', { name: 'Reception navigation' })
    .getByRole('button', { name }).click();
}
async function openReview(page, name = 'Synthetic Accessibility Person') {
  await navigate(page, /Register patient/i);
  await page.locator('#fullName').fill(name);
  await page.getByRole('button', { name: 'Review & continue' }).click();
  const dialog = page.getByRole('dialog');
  await expect(dialog).toBeVisible();
  return dialog;
}
async function register(page) {
  const dialog = await openReview(page);
  await dialog.getByRole('button', { name: 'Confirm new demo registration' }).click();
  await expect(page.locator('.confirmation h2')).toBeVisible();
}
async function openAppointments(page) {
  await navigate(page, /Appointments\s*\/\s*check-in/i);
  await expect(page.getByRole('heading', { name: 'Appointments and check-in', level: 1 })).toBeVisible();
}

test.beforeEach(async ({ page }) => {
  // No external requests, HTTP writes, real patient APIs, or production URLs.
  await page.route('**/*', route => {
    const request = route.request();
    const url = new URL(request.url());
    if (url.origin !== target.origin || !['GET', 'HEAD'].includes(request.method())) {
      return route.abort('blockedbyclient');
    }
    return route.continue();
  });
  const response = await page.goto(baseURL, { waitUntil: 'domcontentloaded' });
  expect(response?.ok()).toBe(true);
  await expect(page.locator('.banner')).toContainText('DEMO MODE');
});

test('R3A-01 semantic landmarks, keyboard Tab, visible focus', async ({ page }) => {
  await expect(page.getByRole('main')).toHaveCount(1);
  await expect(page.getByRole('navigation', { name: 'Reception navigation' })).toHaveCount(1);
  await page.keyboard.press('Tab');
  const focus = await page.evaluate(() => {
    const element = document.activeElement;
    const style = element ? getComputedStyle(element) : null;
    return { tag: element?.tagName, outlineStyle: style?.outlineStyle, outlineWidth: style?.outlineWidth };
  });
  expect(focus.tag).toBe('BUTTON');
  expect(focus.outlineStyle).not.toBe('none');
  expect(parseFloat(focus.outlineWidth)).toBeGreaterThanOrEqual(2);
});

test('R3A-02 invalid registration focuses field and associates announced error', async ({ page }) => {
  await navigate(page, /Register patient/i);
  await page.getByRole('button', { name: 'Review & continue' }).click();
  const field = page.locator('#fullName');
  await expect(field).toBeFocused();
  await expect(field).toHaveAttribute('aria-invalid', 'true');
  await expect(field).toHaveAttribute('aria-describedby', 'nameError');
  await expect(page.locator('#nameError')).toContainText('Enter a valid patient name');
  await expect(page.locator('[aria-live="assertive"]')).toContainText(/errors/i);
});

test('R3A-03 invalid future DOB focuses date and links error', async ({ page }) => {
  await navigate(page, /Register patient/i);
  await page.locator('#fullName').fill('Synthetic Accessibility Person');
  await page.locator('#dobPrecision').selectOption('FULL');
  await page.locator('#dob').fill('2099-01-01');
  await page.getByRole('button', { name: 'Review & continue' }).click();
  const field = page.locator('#dob');
  await expect(field).toBeFocused();
  await expect(field).toHaveAttribute('aria-invalid', 'true');
  await expect(field).toHaveAttribute('aria-describedby', 'dobError');
  await expect(page.locator('#dobError')).not.toBeEmpty();
});

test('R3A-04 modal title focus, Escape dismissal, opener focus restoration', async ({ page }) => {
  const dialog = await openReview(page);
  await expect(page.locator('#reviewTitle')).toBeFocused();
  await expect(dialog).toHaveAttribute('aria-labelledby', 'reviewTitle');
  await page.keyboard.press('Escape');
  await expect(dialog).not.toBeVisible();
  await expect(page.getByRole('button', { name: 'Review & continue' })).toBeFocused();
});

test('R3A-05 modal traps keyboard Tab focus', async ({ page }) => {
  const dialog = await openReview(page);
  for (let index = 0; index < 5; index++) {
    await page.keyboard.press('Tab');
    expect(await page.evaluate(() =>
      !!document.querySelector('dialog')?.contains(document.activeElement)
    )).toBe(true);
  }
  await expect(dialog).toBeVisible();
});

test('R3A-06 successful registration focuses confirmation heading', async ({ page }) => {
  await register(page);
  await expect(page.locator('.confirmation h2')).toBeFocused();
  await expect(page.getByText(/temporary browser memory/i).first()).toBeVisible();
});

test('R3A-07 appointment field labels and invalid-action announcement', async ({ page }) => {
  await openAppointments(page);
  for (const id of ['apt-patient', 'apt-doctor', 'apt-date', 'apt-slot']) {
    const field = page.locator('#' + id);
    await expect(field).toBeVisible();
    const label = await field.evaluate(el => el.labels?.[0]?.textContent?.trim() || '');
    expect(label.length).toBeGreaterThan(5);
  }
  await page.getByRole('button', { name: 'Book DEMO appointment' }).click();
  const feedback = page.locator('[role="status"][tabindex="-1"]');
  await expect(feedback).toBeFocused();
  await expect(feedback).toHaveAttribute('aria-live', 'polite');
  await expect(page.locator('#apt-error')).toBeVisible();
  await expect(page.locator('form[aria-describedby="apt-error"]')).toHaveCount(1);
});

test('R3A-08 accessible appointment actions and Enter-opened history', async ({ page }) => {
  await openAppointments(page);
  await page.locator('#apt-patient').selectOption('DEMO-0001');
  await page.locator('#apt-doctor').selectOption('SYN-D01');
  await page.locator('#apt-date').fill(todayIndia());
  await page.locator('#apt-slot').selectOption('09:00');
  await page.getByRole('button', { name: 'Book DEMO appointment' }).click();
  const card = page.locator('article.appointment-card').first();
  await expect(card).toContainText('Appointment status: Booked');
  for (const name of [/Reschedule DEMO-APT-/i, /Cancel DEMO-APT-/i, /Check in DEMO-APT-/i]) {
    await expect(card.getByRole('button', { name })).toBeVisible();
  }
  const summary = card.locator('summary');
  await summary.focus();
  await page.keyboard.press('Enter');
  await expect(summary.locator('..')).toHaveAttribute('open', '');
  await expect(card).toContainText('Booked:');
});

for (const size of [
  { width: 1440, height: 900 },
  { width: 768, height: 1024 },
  { width: 390, height: 844 },
  { width: 320, height: 568 },
]) {
  test('R3A-09 responsive landmarks and no document overflow at ' + size.width + 'px', async ({ page }) => {
    await page.setViewportSize(size);
    for (const [name, heading] of [
      [/Overview/i, 'Good morning, Reception'],
      [/Register patient/i, 'New patient registration'],
      [/Appointments\s*\/\s*check-in/i, 'Appointments and check-in'],
    ]) {
      await navigate(page, name);
      await expect(page.getByRole('heading', { level: 1, name: heading })).toBeVisible();
      const sizes = await page.evaluate(() => ({
        scroll: document.documentElement.scrollWidth,
        client: document.documentElement.clientWidth,
      }));
      expect(sizes.scroll - sizes.client, 'overflow on ' + heading + ' at ' + size.width + 'px').toBeLessThanOrEqual(3);
    }
  });
}
