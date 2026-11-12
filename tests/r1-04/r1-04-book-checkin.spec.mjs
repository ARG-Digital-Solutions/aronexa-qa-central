import {test,expect} from '@playwright/test';

/**
 * Mocked browser UX only. SQL durability/roles/session checks belong to
 * AppointmentCandidateHttpAcceptanceTests on disposable PostgreSQL 17.
 * Explicit opt-in config prevents default legacy QA suite breakage.
 */
const target=process.env.ARONEXA_CONNECTED_BASE_URL;
if(!target)throw Error('Set local connected preview URL');
const url=new URL(target);
if(url.protocol!=='http:'||!['localhost','127.0.0.1'].includes(url.hostname)
    ||url.pathname!=='/connected-reception-preview.html')
  throw Error('R1-04 browser QA refuses remote/non-preview target');
const id=n=>'11111111-1111-4111-8111-'+String(n).padStart(12,'0');
const tenant=id(1),branch=id(2),registration=id(3),patient=id(4),
      doctor=id(5),appointment=id(6),accessToken='a'.repeat(43);
const reference={tenantId:tenant,branchId:branch,registrationId:registration,patientId:patient};
const localToday=()=>{
  const p=Object.fromEntries(new Intl.DateTimeFormat('en-US',{
    timeZone:'Asia/Kolkata',year:'numeric',month:'2-digit',day:'2-digit',
  }).formatToParts(new Date()).map(x=>[x.type,x.value]));
  return [p.year,p.month,p.day].join('-');
};

async function setup(page,{bookingStatus=201,forgedReceipt=false}={}){
  const visitDate=localToday();
  let bookingCalls=0;
  const stored={...reference,appointmentId:appointment,
    doctorMembershipId:doctor,visitDate,slotStart:'09:00:00',
    stage:'BOOKED',revision:1,replayed:false};
  await page.route('**/*',async route=>{
    const req=route.request(),u=new URL(req.url()),method=req.method();
    if(u.origin!==url.origin)return route.abort('blockedbyclient');
    const path=u.pathname;
    const json=(status,data)=>route.fulfill({
      status,contentType:'application/json',body:JSON.stringify(data),
    });
    if(path==='/api/v1/auth/login'&&method==='POST')
      return json(200,{accessToken,tokenType:'Bearer',
        expiresInSeconds:1800,mustChangePassword:false});
    if(path==='/api/v1/auth/me'&&method==='GET')
      return json(200,{...reference,userId:id(8),membershipId:id(9),
        username:'synthetic_reception',mustChangePassword:false,
        roles:['RECEPTION'],permissions:[
          'PATIENT_REGISTRATION_READ','APPOINTMENT_BOOK',
          'APPOINTMENT_READ','APPOINTMENT_CHECK_IN',
        ]});
    if(path==='/api/v1/auth/logout'&&method==='POST')
      return route.fulfill({status:204,body:''});
    if(path==='/api/v1/branches/'+branch+
       '/patient-registrations/'+registration&&method==='GET')
      return json(200,reference);
    if(path==='/api/v1/branches/'+branch+'/appointments'&&method==='POST'){
      bookingCalls++;
      const body=JSON.parse(req.postData()||'{}');
      if(body.registrationId!==registration
          ||body.doctorMembershipId!==doctor
          ||body.slotStart!=='09:00'
          ||body.visitDate!==visitDate
          ||!/^[a-f0-9-]{36}$/i.test(body.requestId||''))
        return json(400,{code:'INVALID_APPOINTMENT_REQUEST'});
      return json(bookingStatus,bookingStatus===201?{
        ...stored,...(forgedReceipt?{patientId:id(10)}:{}),
      }:{code:'APPOINTMENT_CONFLICT'});
    }
    if(path==='/api/v1/branches/'+branch+'/appointments/'+appointment+'/check-in'
        && method==='POST'){
      if(JSON.parse(req.postData()||'{}').expectedRevision!==1)
        return json(409,{code:'APPOINTMENT_CONFLICT'});
      return json(200,{...stored,stage:'CHECKED_IN',revision:2});
    }
    if(path.startsWith('/api/') || (method!=='GET'&&method!=='HEAD'))
      return route.abort('blockedbyclient');
    return route.continue();
  });
  await page.goto(target);
  await expect(page.getByText(/TEST ONLY — NOT FOR REAL PATIENTS/i)).toBeVisible();
  return {bookingCalls:()=>bookingCalls};
}

async function loginRecover(page){
  await page.getByLabel('Clinic code').fill('test_clinic');
  await page.getByLabel('Staff username').fill('synthetic_reception');
  await page.getByLabel('Staff password').fill('SyntheticOnly-PW!');
  await page.getByLabel('Assigned branch UUID').fill(branch);
  await page.getByRole('checkbox',{name:/disposable test clinic using fictional records only/i}).check();
  await page.getByRole('button',{name:'Sign in and verify session'}).click();
  await expect(page.getByRole('heading',{name:'Find an existing registration'})).toBeVisible();
  await page.getByLabel('Registration ID (UUID)').fill(registration);
  await page.getByRole('button',{name:'Find registration'}).click();
  await expect(page.getByRole('heading',{name:'Existing registration found'})).toBeVisible();
  await page.getByRole('button',{name:'Book test appointment'}).click();
  await expect(page.getByRole('heading',{name:'Book or reopen a saved appointment'})).toBeVisible();
}
async function bookingForm(page){
  await page.getByLabel('Assigned doctor membership UUID').fill(doctor);
  await page.getByLabel('Visit date').fill(localToday());
  await page.getByLabel('Visit slot').selectOption('09:00');
  await page.getByRole('button',{name:'Book test appointment'}).click();
}

test('R1-04 verified registration -> appointment booking -> check-in',async({page})=>{
  const state=await setup(page);
  await loginRecover(page);
  await bookingForm(page);
  await expect(page.getByRole('heading',{name:'Saved appointment',exact:true})).toBeVisible();
  await expect(page.getByRole('region',{name:'Saved appointment'})).toContainText(appointment);
  await expect(page.getByRole('region',{name:'Saved appointment'})).toContainText('BOOKED');
  await page.getByRole('button',{name:'Check in this appointment'}).click();
  await expect(page.getByRole('region',{name:'Saved appointment'})).toContainText('CHECKED_IN');
  await expect(page.getByRole('region',{name:'Saved appointment'})).toContainText('Revision');
  expect(state.bookingCalls()).toBe(1);
  await page.getByRole('button',{name:/Sign out/i}).click();
  await expect(page.getByText(appointment,{exact:true})).toHaveCount(0);
});

test('R1-04 occupied slot stays unconfirmed (no demo fallback)',async({page})=>{
  const state=await setup(page,{bookingStatus:409});
  await loginRecover(page);
  await bookingForm(page);
  await expect(page.getByRole('alert')).toContainText(/slot or appointment state has changed/i);
  // The page title "Book or reopen a saved appointment" contains the
  // substring "Saved appointment". Assert absence of the actual result
  // region, not a partially matching heading.
  await expect(page.getByRole('region',{name:'Saved appointment',exact:true})).toHaveCount(0);
  await expect(page.getByText(appointment,{exact:true})).toHaveCount(0);
  await expect(page.getByRole('heading',{name:'Book or reopen a saved appointment',exact:true})).toBeVisible();
  expect(state.bookingCalls()).toBe(1);
});

test('R1-04 forged patient in booking response is rejected',async({page})=>{
  await setup(page,{forgedReceipt:true});
  await loginRecover(page);
  await bookingForm(page);
  await expect(page.getByRole('alert')).toContainText(/appointment could not be verified/i);
  // The page title "Book or reopen a saved appointment" contains the
  // substring "Saved appointment". Assert absence of the actual result
  // region, not a partially matching heading.
  await expect(page.getByRole('region',{name:'Saved appointment',exact:true})).toHaveCount(0);
  await expect(page.getByText(appointment,{exact:true})).toHaveCount(0);
  await expect(page.getByRole('heading',{name:'Book or reopen a saved appointment',exact:true})).toBeVisible();
});
