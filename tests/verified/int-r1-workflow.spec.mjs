import { test, expect } from '@playwright/test';

// Pinned to PR #61 synthetic-only in-memory demo. No backend access is permitted.
const baseURL = process.env.ARONEXA_BASE_URL ?? 'http://127.0.0.1:5175/';
const u = new URL(baseURL);
if (u.protocol !== 'http:' || !['127.0.0.1', 'localhost'].includes(u.hostname)) {
  throw new Error(`Refusing non-local QA target: ${baseURL}`);
}
const day = (delta = 0) => {
  const p = Object.fromEntries(new Intl.DateTimeFormat('en-US', {
    timeZone:'Asia/Kolkata',year:'numeric',month:'2-digit',day:'2-digit'
  }).formatToParts(new Date()).map(x => [x.type,x.value]));
  return new Date(Date.UTC(+p.year, +p.month - 1, +p.day + delta)).toISOString().slice(0,10);
};
async function openDemo(page) {
  await page.route('**/*', route => {
    const r = route.request(), target = new URL(r.url());
    if (target.origin !== u.origin || !['GET','HEAD'].includes(r.method())) {
      return route.abort('blockedbyclient');
    }
    return route.continue();
  });
  await page.goto(baseURL);
  await expect(page.getByText('DEMO MODE', {exact:true})).toBeVisible();
  await expect(page.getByText(/Data stays in temporary browser memory/i)).toBeVisible();
}
async function register(page, name) {
  await page.getByRole('navigation',{name:'Reception navigation'}).getByRole('button',{name:/Register patient/i}).click();
  await page.locator('#fullName').fill(name);
  await page.getByRole('button',{name:'Review & continue'}).click();
  const dialog = page.getByRole('dialog');
  await expect(dialog).toBeVisible();
  await dialog.getByRole('button',{name:'Confirm new demo registration'}).click();
  await expect(page.getByRole('heading',{name:new RegExp(name)})).toBeVisible();
}
async function book(page, date) {
  await page.getByRole('navigation',{name:'Reception navigation'}).getByRole('button',{name:/Appointments.*check-in/i}).click();
  const patientId = await page.locator('#apt-patient option').filter({hasText:'Synthetic QA Patient'}).first().getAttribute('value');
  expect(patientId).toBeTruthy();
  await page.locator('#apt-patient').selectOption(patientId);
  await page.locator('#apt-doctor').selectOption('SYN-D01');
  await page.locator('#apt-date').fill(date);
  await page.locator('#apt-slot').selectOption('09:00');
  await page.getByRole('button',{name:'Book DEMO appointment'}).click();
  const card=page.locator('article.appointment-card').filter({hasText:'DEMO-APT-0001'});
  await expect(card).toContainText('Appointment status: Booked');
  return card;
}

test('INT-R1 @workflow ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â registration, duplicate review and no auto-merge', async ({page}) => {
  await openDemo(page);
  await register(page,'Synthetic QA Patient');
  await page.getByRole('navigation',{name:'Reception navigation'}).getByRole('button',{name:/Register patient/i}).click();
  await page.locator('#fullName').fill('Synthetic QA Patient');
  await page.getByRole('button',{name:'Review & continue'}).click();
  const dialog=page.getByRole('dialog');
  await expect(dialog).toContainText('Possible existing demo records');
  await expect(dialog).toContainText('Synthetic QA Patient');
  await dialog.getByRole('button',{name:'Review / edit details'}).click();
  await expect(dialog).not.toBeVisible();
});

test('INT-R1 @workflow ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â booking, slot conflict, cancellation and slot release', async ({page}) => {
  await openDemo(page);
  await register(page,'Synthetic QA Patient');
  const card=await book(page,day(1));
  // The booking form still has the values: a duplicate must fail.
  await page.getByRole('button',{name:'Book DEMO appointment'}).click();
  await expect(page.locator('#apt-error')).toContainText(/slot is occupied/i);
  await card.getByRole('button',{name:/^Cancel DEMO-APT-/i}).click();
  await expect(card).toContainText('Appointment status: Cancelled');
  await page.getByRole('button',{name:'Book DEMO appointment'}).click();
  await expect(page.locator('article.appointment-card').filter({hasText:/Appointment status:\s*Booked/})).toHaveCount(1);
});

test('INT-R1 @workflow ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â reschedule preserves a single booking and history', async ({page}) => {
  await openDemo(page);
  await register(page,'Synthetic QA Patient');
  const card=await book(page,day(1));
  await card.getByRole('button',{name:/Reschedule/i}).click();
  await page.locator('#apt-date').fill(day(2));
  await page.locator('#apt-slot').selectOption('09:15');
  await page.getByRole('button',{name:'Save reschedule'}).click();
  await expect(card).toContainText(day(2));
  await expect(card).toContainText('09:15');
  await card.locator('summary').click();
  await expect(card).toContainText(/Rescheduled from/i);
});

test('INT-R1 @workflow ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â check-in only on appointment date, no clinical mutation', async ({page}) => {
  await openDemo(page);
  await register(page,'Synthetic QA Patient');
  const card=await book(page,day(0));
  await card.getByRole('button',{name:/Check in/i}).click();
  await expect(card).toContainText('Appointment status: Checked in');
  const queue=page.locator('section.appointment-section').filter({has:page.getByRole('heading',{name:'Receptionist check-in queue'})});
  await expect(queue).toContainText('Synthetic QA Patient');
  // The patient's clinical status remains Registered; check-in affects appointments only.
  await page.getByRole('navigation',{name:'Reception navigation'}).getByRole('button',{name:'Patient list'}).click();
  await expect(page.getByRole('row').filter({hasText:'Synthetic QA Patient'})).toContainText('Registered');
});
