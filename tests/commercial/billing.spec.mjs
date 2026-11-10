import {test,expect} from '@playwright/test';
import {openPreview} from './helpers.mjs';
test('Billing: doctor denied billing controls',async({page})=>{
 await openPreview(page,'/billing-preview.html');
 await page.locator('#bill-role').selectOption('doctor');
 await expect(page.getByRole('alert')).toContainText('Billing access restricted');
 await expect(page.locator('#bill-fee')).toHaveCount(0);
});
test('Billing: synthetic payment/refund and daily total',async({page})=>{
 await openPreview(page,'/billing-preview.html');
 await page.getByRole('button',{name:'Create synthetic bill'}).click();
 await page.getByRole('button',{name:'Add synthetic payment'}).click();
 await page.locator('#bill-refund-pay').selectOption({index:1});
 await page.getByRole('button',{name:'Record demo refund'}).click();
 await expect(page.getByRole('status')).toContainText('Synthetic refund entry recorded');
 await expect(page.locator('.bill-report')).toContainText('150.00');
 await expect(page.locator('.bill-totals')).toContainText('350.00');
});
test('Billing: reject negative rupee input',async({page})=>{
 await openPreview(page,'/billing-preview.html');
 await page.locator('#bill-fee').fill('-10');
 await page.getByRole('button',{name:'Create synthetic bill'}).click();
 await expect(page.getByRole('status')).toContainText('Enter a valid amount');
});
