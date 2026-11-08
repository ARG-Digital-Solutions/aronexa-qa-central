import { test, expect } from '@playwright/test';
import {
  openLocalApp, syntheticPatient, registerSyntheticPatient, dayInIndia,
  bookForPatient, findAppointment, chooseAvailableSlot, enterNewAppointment,
} from '../support/p01-t07-helpers.mjs';

test.describe('P01-T07 | Integrated appointments browser acceptance', () => {
  test.setTimeout(90_000);
  // Intentional gate: browser tests below create records and alter bookings.
  // Never point the local frontend at the original/shared development database.
  test.skip(
    process.env.ARONEXA_QA_DISPOSABLE_CONFIRMED !== 'YES',
    'Requires isolated disposable synthetic QA backend: set ARONEXA_QA_DISPOSABLE_CONFIRMED=YES only after verifying it.',
  );

  test('QA-004 Book an appointment for the registered patient', async ({ page }) => {
    await openLocalApp(page);
    const patient = syntheticPatient();
    await registerSyntheticPatient(page, patient);
    const booked = await bookForPatient(page, patient, dayInIndia(1));
    const row = await findAppointment(page, patient);
    await expect(row).toContainText(booked.date);
    await expect(row).toContainText(booked.slot);
    await expect(row).toContainText(/Appointment status:\s*Booked/i);
  });

  test('QA-005 Search and reschedule the appointment', async ({ page }) => {
    await openLocalApp(page);
    const patient = syntheticPatient();
    await registerSyntheticPatient(page, patient);
    const original = await bookForPatient(page, patient, dayInIndia(1));
    const row = await findAppointment(page, patient);
    await row.getByRole('button', { name: /^Reschedule\s/i }).click();
    const newDate = dayInIndia(2);
    await page.locator('#apt-date').fill(newDate);
    const newSlot = await chooseAvailableSlot(page);
    await page.getByRole('button', { name: 'Save reschedule' }).click();
    const updated = await findAppointment(page, patient);
    await expect(updated).toContainText(newDate);
    await expect(updated).toContainText(newSlot);
    await expect(updated).toContainText(/Appointment status:\s*Booked/i);
    // History deliberately retains the original date; inspect only the current schedule summary.
    if (original.date !== newDate) {
      const currentSchedule = updated.locator('p').filter({ hasText: newDate }).first();
      await expect(currentSchedule).not.toContainText(original.date);
    }
  });

  test('QA-006 Cancel an appointment and verify slot release', async ({ page }) => {
    await openLocalApp(page);
    const patient = syntheticPatient();
    await registerSyntheticPatient(page, patient);
    const original = await bookForPatient(page, patient, dayInIndia(1));
    const row = await findAppointment(page, patient);
    await row.getByRole('button', { name: /^Cancel\s/i }).click();
    await expect(row).toContainText(/Appointment status:\s*Cancelled/i);
    // Actual UI has no cancellation confirmation dialog and no dynamic slot disabling.
    // Prove slot release functionally by rebooking the same doctor/date/time.
    await enterNewAppointment(page, patient, original.date);
    await page.locator('#apt-slot').selectOption(original.slot);
    await page.getByRole('button', { name: 'Book DEMO appointment' }).click();
    const matching = page.locator('article.appointment-card').filter({ hasText: patient.name });
    await expect(matching).toHaveCount(2);
    await expect(matching.filter({ hasText: /Appointment status:\s*Cancelled/i })).toHaveCount(1);
    await expect(matching.filter({ hasText: /Appointment status:\s*Booked/i })).toHaveCount(1);
  });

  test('QA-007 Check in a patient for an appointment dated today', async ({ page }) => {
    await openLocalApp(page);
    const patient = syntheticPatient();
    await registerSyntheticPatient(page, patient);
    const today = dayInIndia(0);
    await bookForPatient(page, patient, today);
    const row = await findAppointment(page, patient);
    await expect(row).toContainText(today);
    await row.getByRole('button', { name: /^Check in\s/i }).click();
    await expect(row).toContainText(/Appointment status:\s*Checked in/i);
    const queue = page.locator('section.appointment-section').filter({
      has: page.getByRole('heading', { name: 'Receptionist check-in queue' }),
    });
    await expect(queue).toContainText(patient.name);
  });
});
