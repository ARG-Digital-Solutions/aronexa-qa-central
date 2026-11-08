import { expect } from '@playwright/test';

export const SYNTHETIC_NAME = 'Synthetic Automation Patient';

export function isoDateInZone(offsetDays = 0, timeZone = 'Asia/Kolkata') {
  const zoned = new Intl.DateTimeFormat('en-CA', {
    timeZone, year: 'numeric', month: '2-digit', day: '2-digit'
  }).formatToParts(new Date());
  const parts = Object.fromEntries(zoned.map(x => [x.type, x.value]));
  return new Date(Date.UTC(+parts.year, +parts.month - 1, +parts.day + offsetDays))
    .toISOString().slice(0, 10);
}

export async function openHome(page) {
  await page.goto('/');
  await expect(page.getByText(/DEMO MODE/i).first()).toBeVisible();
}

export async function openRegister(page) {
  await openHome(page);
  await page.getByRole('button', { name: /Register patient/i }).first().click();
  await expect(page.getByRole('heading', { name: /New patient registration/i })).toBeVisible();
}

export async function registerDemoPatient(page, name = SYNTHETIC_NAME) {
  await openRegister(page);
  await page.getByRole('textbox', { name: /Patient full name/i }).fill(name);
  await page.getByRole('button', { name: /Review.*continue/i }).click();
  const dialog = page.getByRole('dialog');
  await expect(dialog).toBeVisible();
  await dialog.getByRole('button', { name: /Confirm new demo registration/i }).click();
  await expect(page.getByText(/REGISTRATION COMPLETE/i).first()).toBeVisible();
  return name;
}

export async function openAppointments(page) {
  await openHome(page);
  await page.getByRole('button', { name: /Appointments\s*\/\s*check-?in/i }).click();
  await expect(page.getByRole('heading', { name: /Appointments and check-in/i })).toBeVisible();
}

async function selectFirstValid(select) {
  const options = await select.locator('option').evaluateAll(nodes =>
    nodes.map(x => ({ value: x.value, disabled: x.disabled }))
  );
  const choice = options.find(x => !x.disabled && x.value && !/^select/i.test(x.value));
  if (!choice) throw new Error('No selectable synthetic option found');
  await select.selectOption(choice.value);
}

export async function bookDemoAppointment(page, options = {}) {
  if (!options.alreadyOpen) await openAppointments(page);
  const patient = page.getByRole('combobox', { name: /Demo patient/i });
  const doctor = page.getByRole('combobox', { name: /Synthetic doctor/i });
  await expect(patient).toBeVisible();
  await expect(doctor).toBeVisible();
  await selectFirstValid(patient);
  await selectFirstValid(doctor);
  await page.getByLabel(/Local-calendar date/i).fill(options.date || isoDateInZone(1));
  const slot = page.getByRole('combobox', { name: /Simulated 15-minute slot/i });
  await expect(slot).toBeVisible();
  if (await slot.locator('option[value="13:00"]').count()) await slot.selectOption('13:00');
  else await selectFirstValid(slot);
  await page.getByRole('button', { name: /Book DEMO appointment/i }).click();
  await expect(page.getByText(/DEMO-APT-0001/i).first()).toBeVisible();
}
