import { test, expect } from '@playwright/test';
import { openAppointments, bookDemoAppointment, isoDateInZone } from '../support/helpers.mjs';

test('UI-APT-002 @appointments - new booking and demo token appear', async ({ page }) => {
  await bookDemoAppointment(page);
  await expect(page.getByText(/Appointment status:\s*Booked/i).first()).toBeVisible();
  await expect(page.getByText(/DEMO-APT-0001/i).first()).toBeVisible();
});

test('UI-APT-003 @appointments - same doctor/date/slot conflict rejected', async ({ page }) => {
  await bookDemoAppointment(page);
  await page.getByRole('button', { name: /Book DEMO appointment/i }).click();
  await expect(page.getByText(/1 matching appointments/i)).toBeVisible();
  await expect(page.getByText(/occupied|unavailable|already booked|conflict/i).first()).toBeVisible();
});

test('UI-APT-004 @appointments - search appointment by DEMO token', async ({ page }) => {
  await bookDemoAppointment(page);
  const search = page.getByRole('textbox', { name: /Search patient or DEMO token/i });
  await expect(search).toBeVisible();
  await search.fill('DEMO-APT-0001');
  await expect(page.getByText(/1 matching appointments/i)).toBeVisible();
  await search.fill('NONEXISTENT-DEMO-TOKEN');
  await expect(page.getByText(/0 matching appointments/i)).toBeVisible();
});

test('UI-APT-005 @appointments - past date rejected', async ({ page }) => {
  await openAppointments(page);
  await page.getByLabel(/Local-calendar date/i).fill(isoDateInZone(-2));
  await page.getByRole('button', { name: /Book DEMO appointment/i }).click();
  await expect(page.getByText(/past|invalid date|cannot book|must not/i).first()).toBeVisible();
  await expect(page.getByText(/0 matching appointments/i)).toBeVisible();
});
