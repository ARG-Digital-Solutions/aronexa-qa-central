import {test,expect} from '@playwright/test';
import {openPreview} from './helpers.mjs';
test('Consultation: patient, allergies and synthetic banner',async({page})=>{
 await openPreview(page,'/consultation-preview.html');
 await expect(page.getByRole('heading',{name:'Consultation',exact:true})).toBeVisible();
 await expect(page.getByText('SYNTHETIC DATA ONLY')).toBeVisible();
 await expect(page.getByText('Penicillin (synthetic)')).toBeVisible();
});
test('Consultation: deny receptionist and protect clinical fields',async({page})=>{
 await openPreview(page,'/consultation-preview.html');
 await page.locator('#preview-role').selectOption('receptionist');
 await expect(page.getByRole('alert')).toContainText('Access restricted');
 await expect(page.locator('#consult-complaint')).toHaveCount(0);
});
test('Consultation: versioned draft and patient isolation',async({page})=>{
 await openPreview(page,'/consultation-preview.html');
 await page.locator('#consult-complaint').fill('Fictional symptoms');
 await page.getByRole('button',{name:'Save synthetic draft'}).click();
 await expect(page.getByRole('status')).toContainText('version 1');
 await page.getByRole('button',{name:/Sample Patient Two/}).click();
 await expect(page.locator('#consult-complaint')).toHaveValue('');
});
