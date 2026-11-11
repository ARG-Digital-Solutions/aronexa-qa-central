import { test, expect } from '@playwright/test';
import { openLocalPreview, noHorizontalScroll } from './helpers.mjs';

test('COMM-T06 fictional shared patient follows receptionist → doctor → billing journey', async ({ page }) => {
  await openLocalPreview(page, 'opd-journey-preview.html');
  await expect(page.getByRole('heading', { name: 'One OPD visit, start to finish' })).toBeVisible();
  await expect(page.getByText('SYNTHETIC ONLY · NOT FOR PATIENT CARE')).toBeVisible();
  await expect(page.getByText('SYN-PATIENT-01')).toBeVisible();
  await expect(page.getByText('SYN-ENCOUNTER-01')).toBeVisible();

  for (const label of ['Confirm intake review', 'Book fictional slot', 'Check in patient']) {
    await page.getByRole('button', { name: label }).click();
  }
  await expect(page.getByRole('heading', { name: 'Checked in' })).toBeVisible();
  const history = page.locator('.journey-audit ol li');
  await expect(history).toHaveCount(3);

  await page.getByLabel('Preview persona').selectOption('doctor');
  await page.getByRole('button', { name: 'Save fictional consultation draft' }).click();
  await page.getByRole('button', { name: 'Review fictional Rx draft' }).click();
  await expect(history).toHaveCount(5);

  await page.getByLabel('Preview persona').selectOption('billing');
  await page.getByRole('button', { name: 'Preview fictional bill' }).click();
  await page.getByRole('button', { name: 'View sample daily report' }).click();
  await expect(page.getByText('Fictional workflow preview finished')).toBeVisible();
  await expect(history).toHaveCount(7);
  await expect(page.getByText('SYN-PATIENT-01')).toBeVisible();
  await expect(page.getByText('SYN-ENCOUNTER-01')).toBeVisible();
  await expect(page.getByText('No prescription was issued and no financial transaction occurred.')).toBeVisible();
});

test('COMM-T06 wrong role cannot advance synthetic workflow', async ({ page }) => {
  await openLocalPreview(page, 'opd-journey-preview.html');
  await page.getByLabel('Preview persona').selectOption('doctor');
  await expect(page.getByRole('button', { name: 'Confirm intake review' })).toBeDisabled();
  await expect(page.getByText(/Receptionist must perform this step/)).toBeVisible();
  await expect(page.locator('.journey-audit ol li')).toHaveCount(0);
  await page.getByLabel('Preview persona').selectOption('receptionist');
  await page.getByRole('button', { name: 'Confirm intake review' }).click();
  await expect(page.getByRole('heading', { name: 'Registration reviewed' })).toBeVisible();
  await expect(page.locator('.journey-audit ol li')).toHaveCount(1);
});

test('COMM-T06 browser refresh and reset discard all fictional progress', async ({ page }) => {
  await openLocalPreview(page, 'opd-journey-preview.html');
  await page.getByRole('button', { name: 'Confirm intake review' }).click();
  await page.getByRole('button', { name: 'Book fictional slot' }).click();
  await expect(page.locator('.journey-audit ol li')).toHaveCount(2);
  await page.getByRole('button', { name: 'Reset fictional visit' }).click();
  await expect(page.getByRole('heading', { name: 'Duplicate review' })).toBeVisible();
  await expect(page.locator('.journey-audit ol li')).toHaveCount(0);
  await page.getByRole('button', { name: 'Confirm intake review' }).click();
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Duplicate review' })).toBeVisible();
  await expect(page.locator('.journey-audit ol li')).toHaveCount(0);
});

test('COMM-T06 small-screen and accessible persona control remain usable', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await openLocalPreview(page, 'opd-journey-preview.html');
  const persona = page.getByLabel('Preview persona');
  await persona.focus();
  await expect(persona).toBeFocused();
  await expect(page.getByRole('button', { name: 'Confirm intake review' })).toBeEnabled();
  await noHorizontalScroll(page);
});

test('COMM-T06 preview has explicit no-auth/no-persistence disclaimer', async ({ page }) => {
  await openLocalPreview(page, 'opd-journey-preview.html');
  await expect(page.getByText(/This screen has no login, APIs, prescriptions, billing transactions/i)).toBeVisible();
  await expect(page.getByText(/Actual access control must be enforced by the backend and PostgreSQL/i)).toBeVisible();
});
