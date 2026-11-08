import { expect } from '@playwright/test';
import { randomUUID } from 'node:crypto';

/**
 * AroNexa P01-T07 browser QA helpers.
 * The registration UI fallback selectors are grounded in the GitHub
 * feature/p01-t07c1-reception-demo branch inspected on 2026-11-08.
 * Appointment data-testid selectors are an explicit, proposed UI contract;
 * align them with the latest local appointments worktree before claiming PASS.
 */
export const BASE_URL = process.env.ARONEXA_BASE_URL ?? 'http://127.0.0.1:5174/';
const SAFE_HOSTS = new Set(['127.0.0.1', 'localhost', '[::1]']);

export function assertSafeLocalTarget() {
  const url = new URL(BASE_URL);
  if (!['http:', 'https:'].includes(url.protocol) || !SAFE_HOSTS.has(url.hostname)) {
    throw new Error(`QA blocked: ARONEXA_BASE_URL must be localhost/127.0.0.1; received ${url.origin}`);
  }
}

export function syntheticPatient() {
  const token = randomUUID().replaceAll('-', '').slice(0, 10).toUpperCase();
  return { name: `Synthetic QA ${token}`, dob: '1990-06-15', phone: '' };
}

export function dayInIndia(daysAhead = 0) {
  const target = new Date(Date.now() + daysAhead * 86400_000);
  const parts = new Intl.DateTimeFormat('en-GB', {
    year: 'numeric', month: '2-digit', day: '2-digit', timeZone: 'Asia/Kolkata',
  }).formatToParts(target);
  const obj = Object.fromEntries(parts.map(({ type, value }) => [type, value]));
  return `${obj.year}-${obj.month}-${obj.day}`;
}

// Block any non-local mutation even if the local Vite frontend is inadvertently
// configured to communicate with a remote clinical/production API.
export async function openLocalApp(page) {
  assertSafeLocalTarget();
  await page.route('**/*', route => {
    const request = route.request();
    const method = request.method().toUpperCase();
    const address = new URL(request.url());
    const write = !['GET', 'HEAD', 'OPTIONS'].includes(method);
    if (write && !SAFE_HOSTS.has(address.hostname)) {
      return route.abort('blockedbyclient');
    }
    return route.continue();
  });
  await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });
}

async function clickRegistration(page) {
  const currentButton = page.getByRole('button', {
    name: /Register another patient|Register new patient/i,
  }).first();
  if (await currentButton.count()) {
    await currentButton.click();
  } else {
    await page.getByTestId('patient-register-open').click();
  }
  await expect(page.getByRole('heading', { name: /New patient registration/i })
    .or(page.getByTestId('patient-registration-form')).first()).toBeVisible();
}

async function fillRegistration(page, patient) {
  const fullName = page.locator('#fullName').or(page.getByTestId('patient-full-name')).first();
  await fullName.fill(patient.name);
  const precision = page.locator('#dobPrecision');
  if (await precision.count()) {
    await precision.selectOption('FULL');
  }
  const dob = page.locator('#dob').or(page.getByTestId('patient-date-of-birth')).first();
  if (await dob.count() && await dob.isEnabled()) {
    await dob.fill(patient.dob);
  }
  // Intentionally no real phone number; do not trigger SMS/WhatsApp.
  const review = page.getByRole('button', { name: 'Review & continue' })
    .or(page.getByTestId('patient-registration-review')).first();
  await review.click();
  const dialog = page.getByRole('dialog').or(page.getByTestId('patient-duplicate-review')).first();
  await expect(dialog).toBeVisible();
  return dialog;
}

export async function openRegistrationReview(page, patient) {
  await clickRegistration(page);
  return fillRegistration(page, patient);
}

export async function registerSyntheticPatient(page, patient) {
  const dialog = await openRegistrationReview(page, patient);
  await dialog.getByRole('button', { name: 'Confirm new demo registration' })
    .or(dialog.getByTestId('patient-registration-confirm')).first().click();
  await expect(page.getByRole('heading', { name: new RegExp(`${patient.name} added to reception`, 'i') })
    .or(page.getByTestId('patient-registration-success')).first()).toBeVisible();
  return patient;
}

// Proposed stable data-testid UI contract for the integrated appointments worktree.
// This intentionally fails if the feature is absent, rather than faking a PASS.
export async function openAppointments(page) {
  const nav = page.getByRole('navigation', { name: 'Reception navigation' });
  await nav.getByRole('button', { name: /Appointments\s*\/\s*check-in/i }).click();
  await expect(page.getByRole('heading', { name: 'Appointments and check-in', exact: true })).toBeVisible();
  await expect(page.locator('#apt-patient')).toBeVisible();
}

async function selectPatientForAppointment(page, patient) {
  const option = page.locator('#apt-patient option').filter({ hasText: patient.name }).first();
  await expect(option, 'Newly registered synthetic patient missing from appointment selector').toHaveCount(1);
  const id = await option.getAttribute('value');
  if (!id) throw new Error('Synthetic patient option has no value');
  await page.locator('#apt-patient').selectOption(id);
}

export async function chooseAvailableSlot(page) {
  // Actual UI renders a native <select>; booking logic rejects occupied slots.
  const available = await page.locator('#apt-slot option').evaluateAll(options =>
    options.filter(option => option.value && !option.disabled).map(option => option.value)
  );
  if (!available.length) throw new Error('No selectable demo time slots');
  const slot = available[0];
  await page.locator('#apt-slot').selectOption(slot);
  return slot;
}

export async function bookForPatient(page, patient, date) {
  await openAppointments(page);
  await selectPatientForAppointment(page, patient);
  await page.locator('#apt-doctor').selectOption({ index: 1 });
  await page.locator('#apt-date').fill(date);
  const slot = await chooseAvailableSlot(page);
  await page.getByRole('button', { name: 'Book DEMO appointment' }).click();
  const row = await findAppointment(page, patient);
  await expect(row).toContainText(/Appointment status:\s*Booked/i);
  return { date, slot };
}

export async function findAppointment(page, patient) {
  await page.locator('#apt-search').fill(patient.name);
  const row = page.locator('article.appointment-card').filter({ hasText: patient.name }).first();
  await expect(row).toBeVisible();
  return row;
}

export async function enterNewAppointment(page, patient, date) {
  // Booking form stays visible; no separate 'Create' button exists in this UI.
  await selectPatientForAppointment(page, patient);
  await page.locator('#apt-doctor').selectOption({ index: 1 });
  await page.locator('#apt-date').fill(date);
}
