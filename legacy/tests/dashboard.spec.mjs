import { test, expect } from '@playwright/test';
import { openHome, openAppointments } from '../support/helpers.mjs';

test('UI-C1-001 @smoke @registration - dashboard and demo safeguards display', async ({ page }, testInfo) => {
  await openHome(page);
  await expect(page.getByRole('heading', { name: /Good morning, Reception/i })).toBeVisible();
  await expect(page.getByRole('button', { name: /Register patient/i }).first()).toBeVisible();
  await expect(page.getByText(/Synthetic records only/i).first()).toBeVisible();
  await testInfo.attach('reception-dashboard', { body: await page.screenshot({ fullPage: true }), contentType: 'image/png' });
});

test('UI-APT-001 @smoke @appointments - appointment and check-in screen renders', async ({ page }, testInfo) => {
  await openAppointments(page);
  await expect(page.getByRole('heading', { name: /Book a DEMO appointment/i })).toBeVisible();
  await expect(page.getByText(/Session appointments/i).first()).toBeVisible();
  await expect(page.getByText(/Receptionist check-in queue/i).first()).toBeVisible();
  await testInfo.attach('appointment-screen', { body: await page.screenshot({ fullPage: true }), contentType: 'image/png' });
});
