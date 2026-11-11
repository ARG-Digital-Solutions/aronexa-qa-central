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
  const report = page.locator('.bill-report');
  const totals = page.locator('.bill-totals');
  for (const [panel, label, amount] of [
    [report, 'Invoices', '1'],
    [report, 'Billed', '₹500.00'],
    [report, 'Payments', '₹250.00'],
    [report, 'Refunds', '₹100.00'],
    [report, 'Net collections', '₹150.00'],
    [totals, 'Total fees', '₹500.00'],
    [totals, 'Net paid', '₹150.00'],
    [totals, 'Outstanding', '₹350.00'],
  ]) {
    const value = panel.locator('div').filter({ has: page.getByText(label, {exact:true}) }).locator('strong');
    await expect(value).toHaveText(amount);
  }
  const history = page.getByRole('table', {name:'Append-only demonstration transaction history'});
  const payment = history.getByRole('row').filter({ has: page.getByRole('cell', {name:'PAYMENT',exact:true}) });
  const refund = history.getByRole('row').filter({ has: page.getByRole('cell', {name:'REFUND',exact:true}) });
  await expect(payment.getByRole('cell').nth(2)).toHaveText('₹250.00');
  await expect(refund.getByRole('cell').nth(2)).toHaveText('₹100.00');
  const paymentReference = await payment.getByRole('cell').nth(3).innerText();
  expect(paymentReference.trim()).not.toBe('');
  await expect(refund.getByRole('cell').nth(3)).toHaveText(paymentReference);
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

test('COMM-T04 negative rupee input is rejected without creating an invoice', async ({page}) => {
  await openLocalPreview(page, 'billing-preview.html');
  await page.locator('#bill-fee').fill('-10');
  await page.getByRole('button',{name:'Create synthetic bill'}).click();
  await expect(page.getByRole('status')).toContainText('Enter a valid amount');
  await expect(page.getByText('Start by creating a synthetic bill above.')).toBeVisible();
});
