/**
 * AroNexa P01-T07 QA-only appointment UI contract alignment.
 * Run from the AroNexa-QA-Automation directory with: node path/to/this-file.mjs
 * Preserves existing registration helpers and the disposable-QA skip gate.
 * Writes timestamped backups before modifying two QA files.
 * Does NOT modify the AroNexa frontend, Git branches, or any database.
 */
import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const helperFile = path.join(root, 'support', 'p01-t07-helpers.mjs');
const specFile = path.join(root, 'tests', 'p01-t07-appointments.spec.mjs');

function mustExist(file) {
  if (!fs.existsSync(file)) throw new Error(`Expected QA file is missing: ${file}\nRun this script from the AroNexa-QA-Automation directory.`);
  return fs.readFileSync(file, 'utf8');
}
const helpers = mustExist(helperFile);
const spec = mustExist(specFile);
const marker = 'export async function openAppointments(page) {';
const start = helpers.indexOf(marker);
const testStart = spec.indexOf("  test('QA-004 Book an appointment for the registered patient'");
if (start === -1 || !helpers.includes('export async function enterNewAppointment(page, patient, date)')) {
  throw new Error('Existing appointment helper differs from the expected original. No files were modified.');
}
if (testStart === -1 || !spec.includes("process.env.ARONEXA_QA_DISPOSABLE_CONFIRMED !== 'YES'")) {
  throw new Error('Appointment test source differs from the expected original or the safety gate is missing. No files were modified.');
}
if (!spec.includes('QA-005 Search and reschedule') || !spec.includes('QA-006 Cancel') || !spec.includes('QA-007 Check in')) {
  throw new Error('Expected QA-004 to QA-007 tests are missing. No files were modified.');
}

// Role/label-based locators are taken from the inspected agent-04 App.tsx.
const appointmentHelpers = String.raw`export async function openAppointments(page) {
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
`;

const testCases = String.raw`  test('QA-004 Book an appointment for the registered patient', async ({ page }) => {
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
`;

const newHelpers = helpers.slice(0, start) + appointmentHelpers;
const newSpec = spec.slice(0, testStart) + testCases;
const stamp = new Date().toISOString().replace(/[:.]/g, '-');
for (const file of [helperFile, specFile]) {
  const backup = `${file}.bak-${stamp}`;
  fs.copyFileSync(file, backup, fs.constants.COPYFILE_EXCL);
  console.log(`Backup: ${backup}`);
}
fs.writeFileSync(helperFile, newHelpers, 'utf8');
fs.writeFileSync(specFile, newSpec, 'utf8');
console.log('QA-only locator/test-contract patch applied. Disposable safety gate preserved.');
console.log('Run QA-004 in desktop Chromium first; do not merge or modify the frontend/database.');
