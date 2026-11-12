import {test,expect} from '@playwright/test';

// R1-05 opt-in browser UI tests. API is mocked, no clinical backend,
// patient data or customer installation is used. Real DB is tested separately.
const target=process.env.ARONEXA_CONNECTED_BASE_URL;
if(!target)throw Error('Set ARONEXA_CONNECTED_BASE_URL');
const url=new URL(target);
if(url.protocol!=='http:'||!['127.0.0.1','localhost'].includes(url.hostname)
  ||url.pathname!=='/connected-reception-preview.html')
  throw Error('Refuse non-loopback/non-Reception QA target');
const id=n=>'11111111-1111-4111-8111-'+String(n).padStart(12,'0');
const tenant=id(1),branch=id(2),patient=id(3),registration=id(4),
  doctor=id(5),appointment=id(6),accessToken='a'.repeat(43);
const today=()=>{
  const values=Object.fromEntries(new Intl.DateTimeFormat('en-US',{
    timeZone:'Asia/Kolkata',year:'numeric',month:'2-digit',day:'2-digit',
  }).formatToParts(new Date()).map(p=>[p.type,p.value]));
  return [values.year,values.month,values.day].join('-');
};

async function setup(page,{occupied=false,forged=false,queueDenied=false}={}){
  let saved={tenantId:tenant,branchId:branch,patientId:patient,
    registrationId:registration,appointmentId:appointment,
    doctorMembershipId:doctor,stage:'BOOKED',visitDate:today(),
    slotStart:'09:00:00',revision:1,replayed:false};
  let queueReads=0,mutations=0;
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
      return json(200,{tenantId:tenant,userId:id(8),membershipId:id(9),
        username:'synthetic_reception',mustChangePassword:false,
        roles:['RECEPTION'],permissions:[
          'APPOINTMENT_BOOK','APPOINTMENT_READ','APPOINTMENT_CHECK_IN',
          'APPOINTMENT_RESCHEDULE','APPOINTMENT_CANCEL',
        ]});
    if(path==='/api/v1/auth/logout'&&method==='POST')
      return route.fulfill({status:204,body:''});
    const root='/api/v1/branches/'+branch+'/appointments';
    if(path===root&&method==='GET'){
      queueReads++;
      if(queueDenied)return json(403,{code:'APPOINTMENT_DENIED'});
      const day=u.searchParams.get('visitDate');
      if(day!==today())return json(200,[]);
      return json(200,saved.stage==='CANCELLED'?[]:[
        {...saved,...(forged?{tenantId:id(99)}:{})},
      ]);
    }
    if(path===root+'/'+appointment&&method==='GET')
      return json(200,saved);
    if(path===root+'/'+appointment+'/reschedule'&&method==='POST'){
      mutations++;
      if(occupied)return json(409,{code:'APPOINTMENT_CONFLICT'});
      const body=JSON.parse(req.postData()||'{}');
      if(body.expectedRevision!==saved.revision
        ||body.slotStart!=='09:15'||body.doctorMembershipId!==doctor)
        return json(400,{code:'INVALID_APPOINTMENT_REQUEST'});
      saved={...saved,visitDate:body.visitDate,
        slotStart:body.slotStart+':00',revision:saved.revision+1};
      return json(200,saved);
    }
    if(path===root+'/'+appointment+'/cancel'&&method==='POST'){
      mutations++;
      const body=JSON.parse(req.postData()||'{}');
      if(body.expectedRevision!==saved.revision)
        return json(409,{code:'APPOINTMENT_CONFLICT'});
      saved={...saved,stage:'CANCELLED',revision:saved.revision+1};
      return json(200,saved);
    }
    if(path.startsWith('/api/')||(method!=='GET'&&method!=='HEAD'))
      return route.abort('blockedbyclient');
    return route.continue();
  });
  await page.goto(target);
  await expect(page.getByText(/TEST ONLY — NOT FOR REAL PATIENTS/i)).toBeVisible();
  return {queueReads:()=>queueReads,mutations:()=>mutations};
}

async function signInQueue(page){
  await page.getByLabel('Clinic code').fill('test_clinic');
  await page.getByLabel('Staff username').fill('synthetic_reception');
  await page.getByLabel('Staff password').fill('SyntheticOnly-PW!');
  await page.getByLabel('Assigned branch UUID').fill(branch);
  await page.getByRole('checkbox',{name:/disposable test clinic using fictional records only/i}).check();
  await page.getByRole('button',{name:'Sign in and verify session'}).click();
  await expect(page.getByRole('heading',{name:'Daily appointment queue',exact:true})).toBeVisible();
}

async function showSaved(page){
  await page.getByRole('button',{name:'Load daily queue'}).click();
  await expect(page.getByRole('list',{name:'Appointments for selected day'})).toBeVisible();
  await page.getByRole('button',{name:'Manage appointment'}).click();
  await expect(page.getByRole('region',{name:'Saved appointment',exact:true})).toBeVisible();
}

test('R1-05 daily queue -> reschedule -> confirmed cancellation -> empty queue',async({page})=>{
  const state=await setup(page);
  await signInQueue(page);
  await showSaved(page);
  await expect(page.getByRole('region',{name:'Saved appointment',exact:true}))
    .toContainText('BOOKED');
  await page.getByRole('button',{name:'Reschedule appointment'}).click();
  await page.getByLabel('New visit slot').selectOption('09:15');
  await page.getByRole('button',{name:'Confirm reschedule'}).click();
  await expect(page.getByRole('region',{name:'Saved appointment',exact:true}))
    .toContainText('09:15:00');
  await page.getByRole('button',{name:'Cancel appointment',exact:true}).click();
  await expect(page.getByRole('region',{name:'Confirm appointment cancellation'})).toBeVisible();
  await page.getByRole('button',{name:'Confirm cancellation'}).click();
  await expect(page.getByRole('region',{name:'Saved appointment',exact:true}))
    .toContainText('CANCELLED');
  await page.getByRole('button',{name:'Return to daily queue'}).click();
  await page.getByRole('button',{name:'Load daily queue'}).click();
  await expect(page.getByText('No active appointments for this date.')).toBeVisible();
  expect(state.mutations()).toBe(2);
  expect(state.queueReads()).toBe(2);
});

test('R1-05 denied reschedule clears stale saved receipt and shows refresh queue',async({page})=>{
  const state=await setup(page,{occupied:true});
  await signInQueue(page);
  await showSaved(page);
  await page.getByRole('button',{name:'Reschedule appointment'}).click();
  await page.getByLabel('New visit slot').selectOption('09:15');
  await page.getByRole('button',{name:'Confirm reschedule'}).click();
  await expect(page.getByRole('alert')).toContainText(/slot or appointment state has changed/i);
  await expect(page.getByRole('region',{name:'Saved appointment',exact:true})).toHaveCount(0);
  await expect(page.getByRole('heading',{name:'Daily appointment queue',exact:true})).toBeVisible();
  expect(state.mutations()).toBe(1);
});

test('R1-05 forged queue patient scope is rejected before showing any appointment',async({page})=>{
  await setup(page,{forged:true});
  await signInQueue(page);
  await page.getByRole('button',{name:'Load daily queue'}).click();
  await expect(page.getByRole('alert')).toContainText(/appointment could not be verified/i);
  await expect(page.getByRole('list',{name:'Appointments for selected day'})).toHaveCount(0);
  await expect(page.getByText(appointment,{exact:true})).toHaveCount(0);
});

test('R1-05 server-denied daily queue never renders appointment IDs',async({page})=>{
  await setup(page,{queueDenied:true});
  await signInQueue(page);
  await page.getByRole('button',{name:'Load daily queue'}).click();
  await expect(page.getByRole('alert')).toContainText(/not authorized/i);
  await expect(page.getByRole('list',{name:'Appointments for selected day'})).toHaveCount(0);
});
