import { test, expect } from '@playwright/test';
import { openLocalPreview, noHorizontalScroll } from './helpers.mjs';

test('COMM-T03 wrong role cannot access Rx demo', async ({page}) => {
  await openLocalPreview(page, 'smart-rx-preview.html');
  await expect(page.getByRole('heading',{name:'Prescription workspace',level:1})).toBeVisible();
  await page.locator('#rx-role').selectOption('receptionist');
  await expect(page.getByRole('alert')).toContainText('Access restricted');
  await expect(page.getByRole('button',{name:'Add to draft'})).toHaveCount(0);
});
test('COMM-T03 clinician-entered medicine is a watermarked draft only', async ({page}) => {
  await openLocalPreview(page, 'smart-rx-preview.html');
  for (const [field,value] of Object.entries({
    medicine:'SYN-PLACEBO-TEST', strength:'5 units',form:'Tablet',
    dose:'1 test unit', route:'Oral', frequency:'Once daily', duration:'2 days'
  })) await page.locator('#rx-'+field).fill(value);
  await page.getByRole('button',{name:'Add to draft'}).click();
  await expect(page.getByRole('status')).toContainText('Medicine saved to in-memory draft');
  await page.getByRole('button',{name:'Preview draft'}).click();
  await expect(page.getByRole('region',{name:'Non-clinical draft preview'})).toContainText('INVALID AS PRESCRIPTION');
  await expect(page.getByRole('region',{name:'Non-clinical draft preview'})).toContainText('SYN-PLACEBO-TEST');
});
test('COMM-T03 ink undo/redo and accessible text alternative', async ({page}) => {
  await openLocalPreview(page, 'smart-rx-preview.html');
  const canvas=page.locator('canvas[aria-label^="Drawing surface"]');
  const bounds=await canvas.boundingBox();
  expect(bounds).toBeTruthy();
  await page.mouse.move(bounds.x+20,bounds.y+20);
  await page.mouse.down();
  await page.mouse.move(bounds.x+100,bounds.y+65,{steps:4});
  await page.mouse.up();
  await expect(page.getByRole('status')).toContainText('Ink stroke saved');
  await expect(page.getByText('1 strokes',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Undo'}).click();
  await expect(page.getByText('0 strokes',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Redo'}).click();
  await expect(page.getByText('1 strokes',{exact:true})).toBeVisible();
  await page.locator('#rx-note').fill('Fictional annotation');
  await page.getByRole('button',{name:'Save note to demo'}).click();
  await expect(page.getByRole('status')).toContainText('Free text saved');
  await page.setViewportSize({width:390,height:844});
  await noHorizontalScroll(page);
});
