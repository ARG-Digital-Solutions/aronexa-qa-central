import { test, expect } from '@playwright/test';
import { openHome, openAppointments } from '../support/helpers.mjs';

test('UI-RESP-001 @responsive - reception controls available without page overflow', async ({ page }) => {
  await openHome(page);
  await expect(page.getByRole('button', { name: /Register patient/i }).first()).toBeVisible();
  const overflowing = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2);
  expect(overflowing, 'Main document should not overflow horizontally; inner tables may scroll').toBe(false);
});

test('UI-RESP-002 @responsive - appointment booking controls remain visible', async ({ page }) => {
  await openAppointments(page);
  await expect(page.getByRole('button', { name: /Book DEMO appointment/i })).toBeEnabled();
  await expect(page.getByRole('combobox', { name: /Synthetic doctor/i })).toBeVisible();
});
