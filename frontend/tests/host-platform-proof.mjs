/** Uses the second section of the disposable readiness seed. */
import assert from 'node:assert/strict';
import {mkdir, writeFile} from 'node:fs/promises';
import {chromium} from 'playwright';
const base=process.env.BASE_URL || 'http://127.0.0.1:3000';
assert.equal(new URL(base).hostname,'127.0.0.1');
assert.equal(process.env.MIS_SIM_DISPOSABLE,'1');
const out=process.env.ARTIFACT_DIR || '/tmp/mis-sim-readiness-host';await mkdir(out,{recursive:true});
const b=await chromium.launch();const p=await b.newPage({viewport:{width:1280,height:1000}});
let completed=false;
const errors=[];p.on('pageerror',e=>errors.push(e.message));p.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
p.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`);});
try {
 await p.goto(`${base}/login`);await p.getByLabel('Student ID').fill('M2-201');await p.getByLabel('Password',{exact:true}).fill('StudentPass!2026');await p.getByRole('button',{name:'Sign in',exact:true}).click();await p.waitForURL(`${base}/`);await p.locator('.product-shell').waitFor();
 const token=await p.evaluate(()=>sessionStorage.getItem('mis_sim.access_token'));const headers={Authorization:`Bearer ${token}`};
 const me=await (await p.request.get(`${base}/api/auth/me`,{headers})).json();const prefix=`${base}/api/instances/${me.instance_id}`;
 await p.goto(`${base}/infrastructure`);await p.getByRole('button',{name:'+ New Host Platform',exact:true}).first().click();
 await p.locator('.host-platform-form select').first().selectOption('on_prem');await p.getByLabel('Name',{exact:true}).fill('Readiness platform');
 const created=p.waitForResponse(r=>r.url().endsWith('/host-platforms') && r.request().method()==='POST');await p.getByRole('button',{name:'Create',exact:true}).click();const r=await created;assert.equal(r.status(),200);const platform=(await r.json()).platforms.find(x=>x.name==='Readiness platform');assert.ok(platform);
 await p.getByText('Readiness platform',{exact:true}).click();await p.locator('.platform-detail-modal').waitFor();assert.equal(await p.getByRole('button',{name:'+ Add a Service',exact:true}).count(),1);
 await p.screenshot({path:`${out}/new-platform.png`});
 const rollout=await (await p.request.get(`${prefix}/rollout`,{headers})).json();const asset=rollout.team.deployments[0];
 const attached=await p.request.post(`${prefix}/host-platforms/${platform.id}/members`,{headers,data:{asset_key:asset.id,member_kind:'component'}});assert.equal(attached.status(),200);assert.equal((await attached.json()).platforms.find(x=>x.id===platform.id).members.length,1);
 await p.goto(`${base}/rollout`);await p.getByRole('button',{name:/^view/}).click();await p.locator('.platform-detail-modal').waitFor();
 assert.equal(await p.getByRole('button',{name:'+ Add a Service',exact:true}).count(),0);
 assert.ok((await p.locator('.platform-detail-modal').innerText()).includes(asset.label));
 await p.screenshot({path:`${out}/rollout-platform-readonly.png`,fullPage:true});
 const cross=await p.request.get(`${base}/api/instances/1/host-platforms`,{headers});assert.equal(cross.status(),403);
 const sheet=await (await p.request.get(`${prefix}/review`,{headers})).json();assert.equal((await p.request.post(`${prefix}/review/lock`,{headers,data:{expected_revision:sheet.team.revision}})).status(),200);
 assert.equal((await p.request.patch(`${prefix}/host-platforms/${platform.id}`,{headers,data:{name:'Should not change'}})).status(),409);
 await p.goto(`${base}/infrastructure`);await p.locator('.product-shell').waitFor();assert.equal(await p.getByRole('button',{name:'+ New Host Platform',exact:true}).count(),0);
 await p.setViewportSize({width:720,height:1000});await p.goto(`${base}/rollout`);await p.locator('.product-shell').waitFor();await p.screenshot({path:`${out}/rollout-720-final.png`,fullPage:true});
 assert.deepEqual(errors,[]);completed=true;console.log('PASS host creation, immediate member response, read-only rollout detail, cross-instance refusal, locked writes and 720px final layout');
} finally {await writeFile(`${out}/diagnostics.json`,JSON.stringify({status:completed?"pass":"fail",errors},null,2));await b.close();}
