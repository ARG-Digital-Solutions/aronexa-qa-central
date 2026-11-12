import {test,expect} from '@playwright/test';

// R1-08 independent UI acceptance. All APIs MOCKED, all data fictional.
// Only loopback Vite preview; no real payment, invoice, patient or clinic DB.
const target=process.env.ARONEXA_BILLING_BASE_URL;
if(!target)throw Error('Set ARONEXA_BILLING_BASE_URL before R1-08 browser QA');
const base=new URL(target);
if(base.protocol!=='http:'||!['127.0.0.1','localhost'].includes(base.hostname)
    ||base.pathname!=='/connected-billing-preview.html')
  throw Error('R1-08 billing QA refuses non-local preview');

const id=n=>'11111111-1111-4111-8111-'+String(n).padStart(12,'0');
const tenant=id(1),branch=id(2),patient=id(3),appointment=id(4),
  doctor=id(5),invoiceId=id(6),token='a'.repeat(43);
const fee={tenantId:tenant,branchId:branch,appointmentId:appointment,
  patientId:patient,doctorMembershipId:doctor,
  serviceCode:'OPD-CONSULTATION',
  serviceLabel:'Fictional OPD Consultation',amountPaise:50000};
const reportDay='2026-11-13';

async function setup(page,{noPermission=false,contextDenied=false,
    forgedContext=false,forgedBill=false,creationConflict=false,
    cashConflict=false,booked=false,reportForged=false}={}){
  let bill=null,payCalls=0,billCalls=0;
  await page.route('**/*',async route=>{
    const req=route.request(),url=new URL(req.url()),method=req.method();
    if(url.origin!==base.origin)return route.abort('blockedbyclient');
    const path=url.pathname;
    const json=(status,body)=>route.fulfill({
      status,contentType:'application/json',body:JSON.stringify(body),
    });
    if(path==='/api/v1/auth/login'&&method==='POST')
      return json(200,{accessToken:token,tokenType:'Bearer',
        expiresInSeconds:1800,mustChangePassword:false});
    if(path==='/api/v1/auth/me'&&method==='GET')
      return json(200,{tenantId:tenant,userId:id(9),
        membershipId:id(10),username:'billing_demo',
        roles:noPermission?['RECEPTION']:['BILLING'],
        permissions:noPermission?['APPOINTMENT_READ']:
          ['OPD_BILL_READ','OPD_BILL_CREATE','OPD_PAYMENT_POST','OPD_DAILY_REPORT_READ'],
        mustChangePassword:false});
    if(path==='/api/v1/auth/logout'&&method==='POST')
      return route.fulfill({status:204,body:''});
    const prefix='/api/v1/branches/'+branch+'/appointments/'+appointment;
    if(path===prefix+'/billing-context'&&method==='GET'){
      if(contextDenied)return json(403,{code:'APPOINTMENT_DENIED'});
      if(booked)return json(409,{code:'APPOINTMENT_CONFLICT'});
      return json(200,forgedContext?{...fee,tenantId:id(99)}:fee);
    }
    if(path===prefix+'/bill'&&method==='GET'){
      if(!bill)return route.fulfill({status:404,body:''});
      return json(200,forgedBill?{...bill,patientId:id(99)}:bill);
    }
    if(path===prefix+'/bill'&&method==='POST'){
      billCalls++;
      if(creationConflict)return json(409,{code:'APPOINTMENT_CONFLICT'});
      bill={...fee,invoiceId,invoiceNumber:101,totalPaise:50000,
        paidPaise:0,outstandingPaise:50000,status:'UNPAID',replayed:false};
      return json(201,bill);
    }
    if(path===prefix+'/bill/cash'&&method==='POST'){
      payCalls++;
      if(cashConflict)return json(409,{code:'APPOINTMENT_CONFLICT'});
      const payload=JSON.parse(req.postData()||'{}');
      if(!bill||payload.invoiceId!==bill.invoiceId
          ||payload.amountPaise<1
          ||payload.amountPaise>bill.outstandingPaise)
        return json(409,{code:'APPOINTMENT_CONFLICT'});
      const paid=bill.paidPaise+payload.amountPaise;
      bill={...bill,paidPaise:paid,outstandingPaise:50000-paid,
        status:paid===50000?'PAID':'PARTIAL'};
      return json(200,bill);
    }
    if(path==='/api/v1/branches/'+branch+'/billing/daily'
        &&method==='GET'){
      const day=url.searchParams.get('date');
      const same=day===reportDay;
      const paid=same&&bill?bill.paidPaise:0;
      const response={date:day,tenantId:tenant,branchId:branch,
        invoiceCount:same&&bill?1:0,
        billedPaise:same&&bill?50000:0,
        collectionsPaise:paid,
        outstandingPaise:same&&bill?bill.outstandingPaise:0};
      return json(200,reportForged?{...response,branchId:id(99)}:response);
    }
    if(path.startsWith('/api/')||(method!=='GET'&&method!=='HEAD'))
      return route.abort('blockedbyclient');
    return route.continue();
  });
  await page.goto(target);
  await expect(page.getByText(/TEST ONLY — FICTIONAL BILLING/)).toBeVisible();
  return {payments:()=>payCalls,bills:()=>billCalls};
}

async function login(page){
  await page.getByLabel('Clinic code').fill('test_clinic');
  await page.getByLabel('Billing username').fill('billing_demo');
  await page.getByLabel('Billing password').fill('FictionalBilling-PW!');
  await page.getByLabel('Assigned branch UUID').fill(branch);
  await page.getByRole('checkbox',
    {name:/disposable fictional clinic with no real billing/i}).check();
  await page.getByRole('button',{name:'Sign in to billing'}).click();
  await expect(page.getByRole('heading',
    {name:'OPD Billing & Daily Collections'})).toBeVisible();
}
async function open(page){
  await page.getByLabel('Appointment UUID').fill(appointment);
  await page.getByRole('button',{name:'Open OPD billing'}).click();
}
async function create(page){
  await page.getByRole('button',{name:'Create OPD bill'}).click();
  await expect(page.getByText('Internal bill # 101')).toBeVisible();
}

test('R1-08 server fee -> OPD bill -> partial cash -> reload -> daily report',async({page})=>{
  const state=await setup(page);
  await login(page);await open(page);
  await expect(page.getByText('Authorized clinic fee: ₹500.00')).toBeVisible();
  await create(page);
  await expect(page.getByText('UNPAID',{exact:true})).toBeVisible();
  await page.getByLabel('Cash amount in rupees (₹)').fill('200');
  await page.getByRole('button',{name:'Record fictional cash'}).click();
  await expect(page.getByText('PARTIAL',{exact:true})).toBeVisible();
  await expect(page.getByText('₹300.00')).toBeVisible();
  await page.getByLabel('Clinic date (Asia/Kolkata)').fill(reportDay);
  await page.getByRole('button',{name:'Load daily report'}).click();
  await expect(page.getByRole('region',{name:'Daily collections report'}))
    .toContainText('₹200.00');
  await page.getByRole('button',{name:/Sign out/i}).click();
  await expect(page.getByText('Internal bill # 101')).toHaveCount(0);
  await login(page);await open(page);
  await expect(page.getByText('PARTIAL',{exact:true})).toBeVisible();
  expect(state.payments()).toBe(1);
  expect(state.bills()).toBe(1);
});

test('R1-08 completes cash balance without a real money transfer',async({page})=>{
  const state=await setup(page);
  await login(page);await open(page);await create(page);
  await page.getByLabel('Cash amount in rupees (₹)').fill('500.00');
  await page.getByRole('button',{name:'Record fictional cash'}).click();
  await expect(page.getByText('PAID',{exact:true})).toBeVisible();
  await expect(page.getByLabel('Cash amount in rupees (₹)')).toHaveCount(0);
  expect(state.payments()).toBe(1);
});

test('R1-08 forged patient ID in existing bill is not displayed',async({page})=>{
  await setup(page,{forgedBill:true});
  await login(page);await open(page);await create(page);
  await open(page);
  await expect(page.getByRole('alert')).toContainText(/could not be verified/i);
  await expect(page.getByText('Internal bill # 101')).toHaveCount(0);
});

test('R1-08 wrong tenant in independent billing context blocks bill',async({page})=>{
  const state=await setup(page,{forgedContext:true});
  await login(page);await open(page);
  await expect(page.getByRole('alert')).toContainText(/could not be verified/i);
  await expect(page.getByRole('button',{name:'Create OPD bill'})).toHaveCount(0);
  expect(state.bills()).toBe(0);
});

test('R1-08 denied clinic scope hides fee and all payment controls',async({page})=>{
  await setup(page,{contextDenied:true});
  await login(page);await open(page);
  await expect(page.getByRole('alert')).toContainText(/not authorized/i);
  await expect(page.getByRole('button',{name:'Create OPD bill'})).toHaveCount(0);
  await expect(page.getByLabel('Cash amount in rupees (₹)')).toHaveCount(0);
});

test('R1-08 Reception role cannot open Billing Staff workspace',async({page})=>{
  await setup(page,{noPermission:true});
  await page.getByLabel('Clinic code').fill('test_clinic');
  await page.getByLabel('Billing username').fill('reception_demo');
  await page.getByLabel('Billing password').fill('Fictional-PW!');
  await page.getByLabel('Assigned branch UUID').fill(branch);
  await page.getByRole('checkbox',
    {name:/disposable fictional clinic with no real billing/i}).check();
  await page.getByRole('button',{name:'Sign in to billing'}).click();
  await expect(page.getByRole('alert')).toBeVisible();
  await expect(page.getByRole('button',{name:'Create OPD bill'})).toHaveCount(0);
});

test('R1-08 booked or unconsulted appointment cannot be billed',async({page})=>{
  await setup(page,{booked:true});
  await login(page);await open(page);
  await expect(page.getByRole('alert')).toContainText(/Billing information changed/i);
  await expect(page.getByRole('button',{name:'Create OPD bill'})).toHaveCount(0);
});

test('R1-08 duplicate bill conflict clears stale invoice display',async({page})=>{
  const state=await setup(page,{creationConflict:true});
  await login(page);await open(page);
  await page.getByRole('button',{name:'Create OPD bill'}).click();
  await expect(page.getByRole('alert')).toContainText(/Billing information changed/i);
  await expect(page.getByRole('button',{name:'Create OPD bill'})).toHaveCount(0);
  expect(state.bills()).toBe(1);
});

test('R1-08 cash conflict discards stale amount before retry',async({page})=>{
  const state=await setup(page,{cashConflict:true});
  await login(page);await open(page);await create(page);
  await page.getByLabel('Cash amount in rupees (₹)').fill('300.00');
  await page.getByRole('button',{name:'Record fictional cash'}).click();
  await expect(page.getByRole('alert')).toContainText(/Billing information changed/i);
  await expect(page.getByText('Internal bill # 101')).toHaveCount(0);
  expect(state.payments()).toBe(1);
});

test('R1-08 tampered branch total is rejected without report rendering',async({page})=>{
  await setup(page,{reportForged:true});
  await login(page);
  await page.getByLabel('Clinic date (Asia/Kolkata)').fill(reportDay);
  await page.getByRole('button',{name:'Load daily report'}).click();
  await expect(page.getByRole('alert')).toContainText(/could not be verified/i);
  await expect(page.getByText('Amount billed')).toHaveCount(0);
});
