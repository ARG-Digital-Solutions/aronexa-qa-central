import {test,expect} from '@playwright/test';

// Isolated MOCKED browser UX only. The real HTTP + durable PostgreSQL
// medication snapshot proof is independently executed by Development JUnit.
// No real patient records, third-party sites or prescription issuance.
const target=process.env.ARONEXA_DOCTOR_BASE_URL;
if(!target)throw Error('ARONEXA_DOCTOR_BASE_URL must be set for R1-07');
const base=new URL(target);
if(base.protocol!=='http:'||!['127.0.0.1','localhost'].includes(base.hostname)
  ||base.pathname!=='/connected-doctor-preview.html')
  throw Error('R1-07 refuses non-local/non-doctor preview');

const id=n=>'11111111-1111-4111-8111-'+String(n).padStart(12,'0');
const tenant=id(1),branch=id(2),patient=id(3),appointment=id(4),doctor=id(5),
  accessToken='a'.repeat(43);
const consultNote='FICTIONAL consultation draft — non-clinical';
const medOne='FICTIONAL Medicine Alpha',medTwo='FICTIONAL Medicine Beta';

async function setup(page,{rxDenied=false,forged=false,conflict=false,
                           noPermission=false,consultRevision=1,
                           preConsult=false}={}){
  let rx={tenantId:tenant,branchId:branch,patientId:patient,
    appointmentId:appointment,doctorMembershipId:doctor,
    stage:'EMPTY_DRAFT',revision:0,consultationRevision:1,medicines:[]};
  let saves=0,reads=0;
  await page.route('**/*',async route=>{
    const req=route.request(),url=new URL(req.url()),method=req.method();
    if(url.origin!==base.origin)return route.abort('blockedbyclient');
    const path=url.pathname;
    const json=(status,body)=>route.fulfill({
      status,contentType:'application/json',body:JSON.stringify(body),
    });
    if(path==='/api/v1/auth/login'&&method==='POST')
      return json(200,{accessToken,tokenType:'Bearer',
        expiresInSeconds:1800,mustChangePassword:false});
    if(path==='/api/v1/auth/me'&&method==='GET')
      return json(200,{tenantId:tenant,userId:id(8),membershipId:doctor,
        username:'synthetic_doctor',mustChangePassword:false,
        roles:['DOCTOR'],permissions:noPermission?['OPD_DRAFT_WRITE']:
          ['OPD_DRAFT_WRITE','OPD_RX_DRAFT_WRITE']});
    if(path==='/api/v1/auth/logout'&&method==='POST')
      return route.fulfill({status:204,body:''});
    const prefix='/api/v1/branches/'+branch+'/appointments/'+appointment;
    if(path===prefix+'/consultation-context'&&method==='GET')
      return json(200,{tenantId:tenant,branchId:branch,patientId:patient,
        appointmentId:appointment,doctorMembershipId:doctor,
        appointmentStage:'CHECKED_IN'});
    if(path===prefix+'/consultation-draft'&&method==='GET')
      return json(200,{tenantId:tenant,branchId:branch,patientId:patient,
        appointmentId:appointment,doctorMembershipId:doctor,
        stage:preConsult?'CHECKED_IN':'CONSULTATION_DRAFT',
        revision:preConsult?0:consultRevision,
        consultationNote:preConsult?'':consultNote});
    if(path===prefix+'/prescription-draft'&&method==='GET'){
      reads++;
      if(rxDenied)return json(403,{code:'APPOINTMENT_DENIED'});
      return json(200,forged?{...rx,patientId:id(99)}:rx);
    }
    if(path===prefix+'/prescription-draft'&&method==='POST'){
      saves++;
      if(conflict)return json(409,{code:'APPOINTMENT_CONFLICT'});
      const body=JSON.parse(req.postData()||'{}');
      if(body.expectedRevision!==rx.revision||body.consultationRevision!==1
         ||!Array.isArray(body.medicines)||body.medicines.length<1)
        return json(409,{code:'APPOINTMENT_CONFLICT'});
      rx={...rx,stage:'RX_DRAFT',revision:rx.revision+1,
        medicines:body.medicines};
      return json(200,rx);
    }
    if(path.startsWith('/api/')||(method!=='GET'&&method!=='HEAD'))
      return route.abort('blockedbyclient');
    return route.continue();
  });
  await page.goto(target);
  await expect(page.getByText(/TEST ONLY — NOT FOR REAL PATIENTS/i)).toBeVisible();
  return {saves:()=>saves,reads:()=>reads};
}
async function login(page){
  await page.getByLabel('Clinic code').fill('synthetic_clinic');
  await page.getByLabel('Doctor username').fill('synthetic_doctor');
  await page.getByLabel('Doctor password').fill('Synthetic-PW!');
  await page.getByLabel('Assigned branch UUID').fill(branch);
  await page.getByRole('checkbox',
    {name:/disposable test clinic using fictional notes only/i}).check();
  await page.getByRole('button',{name:'Sign in as doctor'}).click();
  await expect(page.getByRole('heading',
    {name:'Open checked-in appointment',exact:true})).toBeVisible();
}
async function openConsultation(page){
  await page.getByLabel('Checked-in appointment UUID').fill(appointment);
  await page.getByRole('button',{name:'Open consultation'}).click();
  await expect(page.getByRole('region',
    {name:'Doctor consultation draft',exact:true})).toBeVisible();
}
async function openRx(page){
  await page.getByRole('button',{name:'Open prescription draft'}).click();
  await expect(page.getByRole('region',
    {name:'Doctor prescription draft',exact:true})).toBeVisible();
  await expect(page.getByText(/Stage: EMPTY_DRAFT/)).toBeVisible();
}
async function addMedicine(page,name){
  await page.getByLabel('Medicine name').fill(name);
  await page.getByLabel('Strength').fill('FICTIONAL 1');
  await page.getByLabel('Form').fill('tablet');
  await page.getByLabel('Dose',{exact:true}).fill('doctor entered');
  await page.getByLabel('Route').fill('oral');
  await page.getByLabel('Frequency').fill('doctor entered');
  await page.getByLabel('Duration').fill('doctor entered');
  await page.getByLabel('Quantity').fill('1');
  await page.getByLabel('Additional instructions').fill('NOT A REAL PRESCRIPTION');
  await page.getByRole('button',{name:'Add medicine to draft'}).click();
}

test('R1-07 doctor saves fictional structured Rx, signs out, reopens and appends revision',
  async({page})=>{
    const backend=await setup(page);
    await login(page);await openConsultation(page);await openRx(page);
    await addMedicine(page,medOne);
    await page.getByRole('button',{name:'Save prescription draft'}).click();
    await expect(page.getByText(/Prescription draft saved on the test server. Revision 1/i))
      .toBeVisible();
    await page.getByRole('button',{name:/Sign out/i}).click();
    await expect(page.getByText(medOne)).toHaveCount(0);
    await login(page);await openConsultation(page);
    await page.getByRole('button',{name:'Open prescription draft'}).click();
    await expect(page.getByRole('region',{name:'Doctor prescription draft',exact:true}))
      .toContainText(medOne);
    await addMedicine(page,medTwo);
    await page.getByRole('button',{name:'Save prescription draft'}).click();
    await expect(page.getByText(/Prescription draft saved on the test server. Revision 2/))
      .toBeVisible();
    expect(backend.saves()).toBe(2);
    expect(backend.reads()).toBe(2);
    await expect(page.getByText(/DEMO ONLY — INVALID AS PRESCRIPTION/)).toBeVisible();
  });

test('R1-07 Rx denied by server never reveals medicine workspace',async({page})=>{
  await setup(page,{rxDenied:true});
  await login(page);await openConsultation(page);
  await page.getByRole('button',{name:'Open prescription draft'}).click();
  await expect(page.getByRole('alert')).toContainText(/not authorized/i);
  await expect(page.getByLabel('Medicine name')).toHaveCount(0);
});

test('R1-07 valid forged patient UUID in Rx response is rejected',async({page})=>{
  await setup(page,{forged:true});
  await login(page);await openConsultation(page);
  await page.getByRole('button',{name:'Open prescription draft'}).click();
  await expect(page.getByRole('alert')).toContainText(/could not be verified/i);
  await expect(page.getByLabel('Medicine name')).toHaveCount(0);
});

test('R1-07 doctor without Rx permission cannot open Rx editor',async({page})=>{
  const state=await setup(page,{noPermission:true});
  await login(page);await openConsultation(page);
  await expect(page.getByRole('button',{name:'Open prescription draft'})).toHaveCount(0);
  expect(state.reads()).toBe(0);
});

test('R1-07 clinical note is required before prescription can open',async({page})=>{
  const state=await setup(page,{preConsult:true});
  await login(page);await openConsultation(page);
  await expect(page.getByRole('button',{name:'Open prescription draft'})).toHaveCount(0);
  expect(state.reads()).toBe(0);
});

test('R1-07 stale prescription save discards lines and forces server reopening',
  async({page})=>{
    const state=await setup(page,{conflict:true});
    await login(page);await openConsultation(page);await openRx(page);
    await addMedicine(page,medOne);
    await page.getByRole('button',{name:'Save prescription draft'}).click();
    await expect(page.getByRole('alert')).toContainText(/consultation or prescription changed/i);
    await expect(page.getByLabel('Medicine name')).toHaveCount(0);
    await expect(page.getByRole('button',{name:'Reopen server draft'})).toBeVisible();
    expect(state.saves()).toBe(1);
  });

test('R1-07 consultation revision change refuses a previously linked Rx',async({page})=>{
  await setup(page,{consultRevision:2});
  await login(page);await openConsultation(page);
  await page.getByRole('button',{name:'Open prescription draft'}).click();
  await expect(page.getByRole('alert')).toContainText(/could not be verified/i);
  await expect(page.getByLabel('Medicine name')).toHaveCount(0);
});
