import { test, expect } from '@playwright/test';
import { openLocalPreview, noHorizontalScroll } from './helpers.mjs';

test('COMM-T01 doctor sees fictional consultation; receptionist is denied', async ({page}) => {
  await openLocalPreview(page, 'consultation-preview.html');
  await expect(page.getByRole('heading',{name:'Consultation',level:1})).toBeVisible();
  await expect(page.getByText('SYNTHETIC DATA ONLY')).toBeVisible();
  await page.locator('#preview-role').selectOption('receptionist');
  await expect(page.getByRole('alert')).toContainText('Access restricted');
  await expect(page.getByRole('button',{name:'Save synthetic draft'})).toHaveCount(0);
});
test('COMM-T01 save only drafts and reset on patient switch', async ({page}) => {
  await openLocalPreview(page, 'consultation-preview.html');
  await page.locator('#consult-complaint').fill('Fictional follow-up consultation');
  await page.getByRole('button',{name:'Save synthetic draft'}).click();
  await expect(page.getByRole('status')).toContainText('version 1 saved');
  await page.locator('#consult-plan').fill('Synthetic monitoring plan');
  await page.getByRole('button',{name:'Save synthetic draft'}).click();
  await expect(page.getByRole('status')).toContainText('version 2 saved');
  const complaint = page.locator('#consult-complaint');
  const unsavedComplaint = 'Fictional edit to discard';
  await complaint.fill(unsavedComplaint);
  await expect(complaint).toHaveValue(unsavedComplaint);
  await expect(page.getByRole('status')).toContainText('Unsaved changes');
  const nextPatient = page.locator('.consult-patient-choice').last();
  await expect(nextPatient).toHaveAttribute('aria-pressed', 'false');
  await nextPatient.click();
  await expect(nextPatient).toHaveAttribute('aria-pressed', 'true');
  await expect(page.getByRole('status')).toContainText('Unsaved edits');
  await expect(complaint).toHaveValue('');
});
test('COMM-T01 mobile view and explicit draft limitation', async ({page}) => {
  await page.setViewportSize({width:390,height:844});
  await openLocalPreview(page, 'consultation-preview.html');
  await expect(page.getByText(/No persistence, API, prescription/i)).toBeVisible();
  await noHorizontalScroll(page);
});
