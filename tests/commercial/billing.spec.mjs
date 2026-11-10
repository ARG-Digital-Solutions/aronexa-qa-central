import { test, expect } from '@playwright/test';
import { openLocalPreview, noHorizontalScroll } from './helpers.mjs';

test('COMM-T04 doctor is blocked from billing preview', async ({page}) => {
  await openLocalPreview(page, 'billing-preview.html');
  await expect(page.getByRole('heading',{name:'Billing & Daily Reports',level:1})).toBeVisible();
  await page.locator('#bill-role').selectOption('doctor');
  await expect(page.getByRole('alert')).toContainText('Billing access restricted');
  await expect(page.getByRole('button',{name:'Create synthetic bill'})).toHaveCount(0);
});
test('COMM-T04 invoice, partial payment, linked refund reconcile daily report', async ({page}) => {
  await openLocalPreview(page, 'billing-preview.html');
  await page.locator('#bill-fee').fill('500');
  await page.getByRole('button',{name:'Create synthetic bill'}).click();
  await expect(page.getByRole('status')).toContainText('Synthetic invoice created');
  await page.locator('#bill-payment').fill('250');
  await page.getByRole('button',{name:'Add synthetic payment'}).click();
  await expect(page.getByRole('status')).toContainText('Synthetic partial payment added');
  await page.locator('#bill-refund-pay').selectOption({index:1});
  await page.locator('#bill-refund').fill('100');
  await page.getByRole('button',{name:'Record demo refund'}).click();
  await expect(page.getByRole('status')).toContainText('Synthetic refund entry recorded');
  await expect(page.locator('.bill-report')).toContainText('Net collections');
  await expect(page.locator('.bill-report')).toContainText('150');
  await expect(page.locator('.bill-totals')).toContainText('350');
});
test('COMM-T04 reload loses fictional invoices; responsive mobile', async ({page}) => {
  await page.setViewportSize({width:390,height:844});
  await openLocalPreview(page, 'billing-preview.html');
  await page.getByRole('button',{name:'Create synthetic bill'}).click();
  await expect(page.getByRole('status')).toContainText('Synthetic invoice created');
  await page.reload();
  await expect(page.getByText('Start by creating a synthetic bill above.')).toBeVisible();
  await noHorizontalScroll(page);
});
