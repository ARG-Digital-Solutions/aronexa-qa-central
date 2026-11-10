import {expect} from '@playwright/test';
export async function openPreview(page,path){
  const origin=new URL(process.env.ARONEXA_BASE_URL??'http://127.0.0.1:5175/').origin;
  await page.route('**/*',route=>{
    const request=route.request();
    let url;
    try{url=new URL(request.url());}catch{return route.abort('blockedbyclient');}
    return url.origin===origin&&['GET','HEAD'].includes(request.method())?route.continue():route.abort('blockedbyclient');
  });
  await page.goto(origin+path);
  await expect(page.locator('body')).toBeVisible();
}
