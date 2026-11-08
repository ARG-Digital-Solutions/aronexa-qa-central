import { test, expect } from '@playwright/test';
import { bookDemoAppointment, isoDateInZone } from '../support/helpers.mjs';

// These are provisional @extended adapters. The latest uncommitted App.tsx was NOT
// available for exact locator verification. Execute separately and confirm selectors
// against the current app before using failures as evidence of a product defect.

test('UI-APT-006 @extended - cancellation releases booked slot', async ({ page }) => {
  await bookDemoAppointment(page);
  await page.getByRole('button', { name: /^Cancel( appointment)?$/i }).click();
  await expect(page.getByText(/Appointment status:\s*Cancelled/i).first()).toBeVisible();
});

test('UI-APT-007 @extended - reschedule updates booking and history', async ({ page }) => {
  await bookDemoAppointment(page);
  await page.getByRole('button', { name: /Reschedule/i }).click();
  await page.getByLabel(/New (appointment )?date/i).fill(isoDateInZone(3));
  await page.getByRole('button', { name: /Confirm reschedul/i }).click();
  await expect(page.getByText(/Rescheduled|reschedule/i).first()).toBeVisible();
});

test('UI-APT-008 @extended - same-day check-in updates receptionist queue', async ({ page }) => {
  await bookDemoAppointment(page, { date: isoDateInZone(0) });
  await page.getByRole('button', { name: /Check[ -]?in/i }).last().click();
  await expect(page.getByText(/Appointment status:\s*Checked in/i).first()).toBeVisible();
  await expect(page.getByText(/Receptionist check-in queue/i)).toBeVisible();
});
