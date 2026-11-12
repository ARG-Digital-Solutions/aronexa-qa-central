import {test,expect} from '@playwright/test';

/**
 * Isolated connected-Reception browser UX, fictional data only.
 * HTTP responses are mocked here, never presented as DB persistence proof.
 * Actual committed rows/auth/read audit are covered in the Java+Node
 * PostgreSQL Testcontainers suite in application PR R1-03.
 */
const base=process.env.ARONEXA_CONNECTED_BASE_URL
  ?? 'http://127.0.0.1:5176/connected-reception-preview.html';
const u=new URL(base);
if(u.protocol!=='http:' || !['127.0.0.1','localhost'].includes(u.hostname)
  || u.pathname!=='/connected-reception-preview.html'){
  throw new Error('Refusing non-local or non-connected Reception QA target');
}
const id=n=>'11111111-1111-4111-8111-'+String(n).padStart(12,'0');
const tenant=id(1),branch=id(2),registration=id(3),patient=id(4);
const token='a'.repeat(43);
const me={tenantId:tenant,userId:id(5),membershipId:id(6),
  username:'synthetic_reception',mustChangePassword:false,
  roles:['RECEPTION'],permissions:['PATIENT_REGISTRATION_READ']};
const reference={tenantId:tenant,branchId:branch,registrationId:registration,patientId:patient};

async function setup(page,getStatus=()=>200,getReference=()=>reference){
  await page.route('**/*',async route=>{
    const req=route.request(),url=new URL(req.url()),method=req.method();
    if(url.origin!==u.origin)return route.abort('blockedbyclient');
    const path=url.pathname;
    if(path==='/api/v1/auth/login' && method==='POST'){
      return route.fulfill({status:200,contentType:'application/json',
        body:JSON.stringify({accessToken:token,tokenType:'Bearer',
          expiresInSeconds:1800,mustChangePassword:false})});
    }
    if(path==='/api/v1/auth/me' && method==='GET'){
      if(req.headers().authorization!=='Bearer '+token){
        return route.fulfill({status:401,body:''});
      }
      return route.fulfill({status:200,contentType:'application/json',
        body:JSON.stringify(me)});
    }
    if(path==='/api/v1/branches/'+branch+'/patient-registrations/'+registration
      && method==='GET'){
      if(req.headers().authorization!=='Bearer '+token){
        return route.fulfill({status:401,body:''});
      }
      return route.fulfill({status:getStatus(),contentType:'application/json',
        body:JSON.stringify(getReference())});
    }
    if(path==='/api/v1/auth/logout' && method==='POST')
      return route.fulfill({status:204,body:''});
    if(path.startsWith('/api/') || (method!=='GET'&&method!=='HEAD'))
      return route.abort('blockedbyclient');
    return route.continue();
  });
  await page.goto(base);
  await expect(page.getByText(/TEST ONLY — NOT FOR REAL PATIENTS/i)).toBeVisible();
}

async function signInAsReadOnly(page){
  await page.getByLabel('Clinic code').fill('test_clinic');
  await page.getByLabel('Staff username').fill('synthetic_reception');
  await page.getByLabel('Staff password').fill('SyntheticSecret-123!');
  await page.getByLabel('Assigned branch UUID').fill(branch);
  await page.getByRole('checkbox',{
    name:/disposable test clinic using fictional records only/i,
  }).check();
  await page.getByRole('button',{name:'Sign in and verify session'}).click();
  await expect(page.getByRole('heading',{name:'Find an existing registration'}))
    .toBeVisible();
}

test('R1-03 read-only staff can find durable registration reference, then sign out',async({page})=>{
  await setup(page);
  await signInAsReadOnly(page);
  await page.getByLabel('Registration ID (UUID)').fill(registration);
  await page.getByRole('button',{name:'Find registration'}).click();
  await expect(page.getByRole('heading',{name:'Existing registration found'})).toBeVisible();
  await expect(page.getByRole('region',{name:'Verified existing registration'}))
    .toContainText(patient);
  await expect(page.getByRole('region',{name:'Verified existing registration'}))
    .toContainText(registration);
  await expect(page.getByText(/cannot create an appointment or authorize clinical care/i))
    .toBeVisible();
  await page.getByRole('button',{name:/Sign out/i}).click();
  await expect(page.getByRole('heading',{name:'Staff sign-in'})).toBeVisible();
  await expect(page.getByText(patient,{exact:true})).toHaveCount(0);
  await page.reload();
  await expect(page.getByRole('heading',{name:'Staff sign-in'})).toBeVisible();
});

test('R1-03 denied read never shows a patient reference',async({page})=>{
  await setup(page,()=>403);
  await signInAsReadOnly(page);
  await page.getByLabel('Registration ID (UUID)').fill(registration);
  await page.getByRole('button',{name:'Find registration'}).click();
  await expect(page.getByRole('alert'))
    .toContainText(/unavailable to your current role or branch/i);
  await expect(page.getByText(patient,{exact:true})).toHaveCount(0);
});

test('R1-03 wrong-tenant server receipt fails closed',async({page})=>{
  await setup(page,()=>200,()=>({...reference,tenantId:id(7)}));
  await signInAsReadOnly(page);
  await page.getByLabel('Registration ID (UUID)').fill(registration);
  await page.getByRole('button',{name:'Find registration'}).click();
  await expect(page.getByRole('alert'))
    .toContainText(/registration could not be verified/i);
  await expect(page.getByText(patient,{exact:true})).toHaveCount(0);
});

test('R1-03 malformed demo ID cannot request a patient from server',async({page})=>{
  let lookups=0;
  await setup(page,()=>{lookups++;return 200;});
  await signInAsReadOnly(page);
  await page.getByLabel('Registration ID (UUID)').fill('DEMO-0001');
  await page.getByRole('button',{name:'Find registration'}).click();
  await expect(page.getByRole('alert')).toContainText(/valid registration UUID/i);
  expect(lookups).toBe(0);
});
