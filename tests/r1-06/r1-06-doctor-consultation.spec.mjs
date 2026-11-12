import {test,expect} from '@playwright/test';

// Independent BROWSER UX only: every /api/v1 response is mocked.
// Database persistence is proved separately by disposable PG17 HTTP JUnit.
const target=process.env.ARONEXA_DOCTOR_BASE_URL;
if(!target)throw Error('Set ARONEXA_DOCTOR_BASE_URL to local doctor preview');
const base=new URL(target);
if(base.protocol!=='http:'||!['127.0.0.1','localhost'].includes(base.hostname)
  ||base.pathname!=='/connected-doctor-preview.html')
  throw Error('Refuse non-loopback/non-doctor QA destination');

const id=n=>'11111111-1111-4111-8111-'+String(n).padStart(12,'0');
const tenant=id(1),branch=id(2),patient=id(3),appointment=id(4),
  doctor=id(5),accessToken='a'.repeat(43);
const noteInitial='FICTIONAL doctor consultation one';
const noteUpdated='FICTIONAL doctor consultation two';

async function setup(page,{denied=false,notCheckedIn=false,
                           forged=false,conflict=false}={}){
  let state={tenantId:tenant,branchId:branch,patientId:patient,
    appointmentId:appointment,doctorMembershipId:doctor,
    stage:'CHECKED_IN',revision:0,consultationNote:''};
  let saves=0;
  await page.route('**/*',async route=>{
    const req=route.request(),u=new URL(req.url()),method=req.method();
    if(u.origin!==base.origin)return route.abort('blockedbyclient');
    const path=u.pathname;
    const json=(status,body)=>route.fulfill({
      status,contentType:'application/json',body:JSON.stringify(body),
    });
    if(path==='/api/v1/auth/login'&&method==='POST'){
      return json(200,{accessToken,tokenType:'Bearer',
        expiresInSeconds:1800,mustChangePassword:false});
    }
    if(path==='/api/v1/auth/me'&&method==='GET'){
      return json(200,{tenantId:tenant,userId:id(7),membershipId:doctor,
        username:'doctor_test',mustChangePassword:false,
        roles:['DOCTOR'],permissions:['OPD_DRAFT_WRITE']});
    }
    if(path==='/api/v1/auth/logout'&&method==='POST'){
      return route.fulfill({status:204,body:''});
    }
    const endpoint='/api/v1/branches/'+branch+'/appointments/'+
      appointment+'/consultation-draft';
    const identityEndpoint='/api/v1/branches/'+branch+'/appointments/'+
      appointment+'/consultation-context';
    if(path===identityEndpoint&&method==='GET'){
      if(denied)return json(403,{code:'APPOINTMENT_DENIED'});
      if(notCheckedIn)return json(409,{code:'APPOINTMENT_CONFLICT'});
      return json(200,{tenantId:tenant,branchId:branch,patientId:patient,
        appointmentId:appointment,doctorMembershipId:doctor,
        appointmentStage:'CHECKED_IN'});
    }
    if(path===endpoint&&method==='GET'){
      if(denied)return json(403,{code:'APPOINTMENT_DENIED'});
      if(notCheckedIn)return json(409,{code:'APPOINTMENT_CONFLICT'});
      return json(200,forged?{...state,patientId:id(90)}:state);
    }
    if(path===endpoint&&method==='POST'){
      saves++;
      const body=JSON.parse(req.postData()||'{}');
      if(conflict||body.expectedRevision!==state.revision)
        return json(409,{code:'APPOINTMENT_CONFLICT'});
      state={...state,stage:'CONSULTATION_DRAFT',
        revision:state.revision+1,consultationNote:body.consultationNote};
      return json(200,state);
    }
    if(path.startsWith('/api/')||(method!=='GET'&&method!=='HEAD'))
      return route.abort('blockedbyclient');
    return route.continue();
  });
  await page.goto(target);
  await expect(page.getByText(/TEST ONLY — NOT FOR REAL PATIENTS/i)).toBeVisible();
  return {saves:()=>saves};
}

async function login(page){
  await page.getByLabel('Clinic code').fill('test_clinic');
  await page.getByLabel('Doctor username').fill('doctor_test');
  await page.getByLabel('Doctor password').fill('SyntheticDoctor-PW!');
  await page.getByLabel('Assigned branch UUID').fill(branch);
  await page.getByRole('checkbox',
    {name:/disposable test clinic using fictional notes only/i}).check();
  await page.getByRole('button',{name:'Sign in as doctor'}).click();
  await expect(page.getByRole('heading',
    {name:'Open checked-in appointment',exact:true})).toBeVisible();
}

async function open(page){
  await page.getByLabel('Checked-in appointment UUID').fill(appointment);
  await page.getByRole('button',{name:'Open consultation'}).click();
}

test('R1-06 doctor opens checked-in appointment, saves, signs out, reopens and revises',
  async({page})=>{
    const backend=await setup(page);
    await login(page);
    await open(page);
    await expect(page.getByRole('region',
      {name:'Doctor consultation draft',exact:true})).toBeVisible();
    await expect(page.getByText('Revision: 0')).toBeVisible();
    await page.getByLabel('Clinical observations (fictional)').fill(noteInitial);
    await page.getByRole('button',{name:'Save consultation draft'}).click();
    await expect(page.getByText('Draft saved and verified on the server. Revision 1.'))
      .toBeVisible();
    await page.getByRole('button',{name:/Sign out/i}).click();
    await expect(page.getByText(noteInitial)).toHaveCount(0);

    await login(page);
    await open(page);
    await expect(page.getByLabel('Clinical observations (fictional)')).toHaveValue(noteInitial);
    await page.getByLabel('Clinical observations (fictional)').fill(noteUpdated);
    await page.getByRole('button',{name:'Save consultation draft'}).click();
    await expect(page.getByText('Draft saved and verified on the server. Revision 2.'))
      .toBeVisible();
    expect(backend.saves()).toBe(2);
  });

test('R1-06 unauthorized doctor cannot read or display draft',async({page})=>{
  await setup(page,{denied:true});
  await login(page);
  await open(page);
  await expect(page.getByRole('alert')).toContainText(/cannot access this consultation/i);
  await expect(page.getByLabel('Clinical observations (fictional)')).toHaveCount(0);
});

test('R1-06 booked appointment cannot create a consultation before check-in',
  async({page})=>{
    await setup(page,{notCheckedIn:true});
    await login(page);
    await open(page);
    await expect(page.getByRole('alert')).toContainText(/consultation state changed/i);
    await expect(page.getByRole('region',
      {name:'Doctor consultation draft',exact:true})).toHaveCount(0);
  });

test('R1-06 forged patient reference is rejected before notes become visible',
  async({page})=>{
    await setup(page,{forged:true});
    await login(page);
    await open(page);
    await expect(page.getByRole('alert')).toContainText(/could not be verified/i);
    await expect(page.getByLabel('Clinical observations (fictional)')).toHaveCount(0);
  });

test('R1-06 conflicting save discards stale draft and requires reopening',
  async({page})=>{
    const backend=await setup(page,{conflict:true});
    await login(page);
    await open(page);
    await page.getByLabel('Clinical observations (fictional)').fill(noteInitial);
    await page.getByRole('button',{name:'Save consultation draft'}).click();
    await expect(page.getByRole('alert')).toContainText(/consultation state changed/i);
    await expect(page.getByRole('heading',
      {name:'Open checked-in appointment',exact:true})).toBeVisible();
    await expect(page.getByLabel('Clinical observations (fictional)')).toHaveCount(0);
    expect(backend.saves()).toBe(1);
  });
