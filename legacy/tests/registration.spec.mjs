import { test, expect } from '@playwright/test';
import { openRegister, registerDemoPatient, SYNTHETIC_NAME } from '../support/helpers.mjs';

test('UI-C1-002 @registration - required name validation visible', async ({ page }) => {
  await openRegister(page);
  await page.getByRole('button', { name: /Review.*continue/i }).click();
  await expect(page.getByText(/Enter a valid patient name/i)).toBeVisible();
  await expect(page.getByRole('dialog')).toHaveCount(0);
});

test('UI-C1-003 @registration - register synthetic patient then find in directory', async ({ page }) => {
  await registerDemoPatient(page, SYNTHETIC_NAME);
  await page.getByRole('button', { name: /View patient list/i }).click();
  await expect(page.getByText(SYNTHETIC_NAME)).toBeVisible();
  await expect(page.getByText(/DEMO-0005/i).first()).toBeVisible();
});

test('UI-C1-004 @registration - duplicate is suggestion, not automatic merge', async ({ page }) => {
  await openRegister(page);
  await page.getByRole('textbox', { name: /Patient full name/i }).fill('Anaya Kulkarni');
  await page.getByRole('button', { name: /Review.*continue/i }).click();
  const dialog = page.getByRole('dialog');
  await expect(dialog).toBeVisible();
  await expect(dialog.getByText(/Anaya Kulkarni/i).first()).toBeVisible();
  await expect(dialog.getByText(/DEMO-0001/i).first()).toBeVisible();
  await dialog.getByRole('button', { name: /Review.*edit details/i }).click();
  await expect(dialog).toHaveCount(0);
});

test('UI-C1-005 @registration - modal Escape restores focus', async ({ page }) => {
  await openRegister(page);
  await page.getByRole('textbox', { name: /Patient full name/i }).fill(SYNTHETIC_NAME);
  await page.getByRole('button', { name: /Review.*continue/i }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page.getByRole('button', { name: /Review.*continue/i })).toBeFocused();
});

test('UI-C1-006 @registration - refresh discards session-created patient', async ({ page }) => {
  await registerDemoPatient(page);
  await page.reload();
  await expect(page.getByText(/DEMO MODE/i).first()).toBeVisible();
  await page.getByRole('button', { name: /Patient list/i }).click();
  await expect(page.getByText(SYNTHETIC_NAME)).toHaveCount(0);
});
