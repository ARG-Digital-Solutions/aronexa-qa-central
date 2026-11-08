import { test, expect } from '@playwright/test';
import {
  openLocalApp,
  syntheticPatient,
  registerSyntheticPatient,
  openRegistrationReview,
} from '../support/p01-t07-helpers.mjs';

test.describe('P01-T07 | Reception and identity browser acceptance', () => {
  test('QA-001 Reception Dashboard opens correctly', async ({ page }) => {
    await openLocalApp(page);
    const heading = page.getByRole('heading', {
      name: /Good morning, Reception|Reception Dashboard/i,
    }).or(page.getByTestId('reception-dashboard')).first();
    await expect(heading).toBeVisible();
    await expect(page.getByRole('button', { name: /Register new patient/i })
      .or(page.getByTestId('patient-register-open')).first()).toBeVisible();
    // The C1 demo identifies itself as synthetic-only. Other increments may use a different banner.
    const demoBanner = page.getByText('DEMO MODE', { exact: true });
    if (await demoBanner.count()) {
      await expect(demoBanner).toBeVisible();
    }
  });

  test('QA-002 Register a new synthetic test patient', async ({ page }) => {
    await openLocalApp(page);
    const patient = syntheticPatient();
    await registerSyntheticPatient(page, patient);
    const viewList = page.getByRole('button', { name: 'View patient list' })
      .or(page.getByTestId('patient-list-open')).first();
    await viewList.click();
    await expect(page.getByRole('row').filter({ hasText: patient.name }).first()
      .or(page.getByTestId('patient-row').filter({ hasText: patient.name }).first()))
      .toBeVisible();
  });

  test('QA-003 Duplicate patient review displays correctly, without auto-merging', async ({ page }) => {
    await openLocalApp(page);
    const patient = syntheticPatient();
    await registerSyntheticPatient(page, patient);
    const dialog = await openRegistrationReview(page, patient);
    await expect(dialog).toContainText(patient.name);
    await expect(dialog).toContainText(/possible|matching|review|duplicate/i);
    // Do not click Confirm: review must be a deliberate receptionist decision.
    const editButton = dialog.getByRole('button', { name: 'Review / edit details' })
      .or(dialog.getByTestId('patient-duplicate-back')).first();
    await editButton.click();
    await expect(dialog).not.toBeVisible();
  });
});
