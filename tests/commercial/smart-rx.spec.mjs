import {test,expect} from '@playwright/test';
import {openPreview} from './helpers.mjs';
test('Rx: denied-role does not expose clinical fields',async({page})=>{
 await openPreview(page,'/smart-rx-preview.html');
 await page.locator('#rx-role').selectOption('receptionist');
 await expect(page.getByRole('alert')).toContainText('Access restricted');
 await expect(page.locator('#rx-dose')).toHaveCount(0);
});
test('Rx: clinician draft cannot become valid prescription',async({page})=>{
 await openPreview(page,'/smart-rx-preview.html');
 const fields={medicine:'Example Tablet A',strength:'example',form:'tablet',dose:'clinician specified',route:'oral',frequency:'clinician specified',duration:'clinician specified'};
 for(const [k,v] of Object.entries(fields))await page.locator('#rx-'+k).fill(v);
 await page.getByRole('button',{name:'Add to draft'}).click();
 await page.getByRole('button',{name:'Preview draft'}).click();
 await expect(page.getByRole('region',{name:'Non-clinical draft preview'})).toContainText('INVALID AS PRESCRIPTION');
});
test('Rx: keyboard-accessible clinical note alternative',async({page})=>{
 await openPreview(page,'/smart-rx-preview.html');
 await page.locator('#rx-note').fill('Fictional note');
 await page.getByRole('button',{name:'Save note to demo'}).click();
 await expect(page.getByRole('status')).toContainText('Free text saved');
});
