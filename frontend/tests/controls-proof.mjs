/** Uses team four of the disposable readiness cohort; leaves its sheet unlocked. */
import assert from 'node:assert/strict';
import {mkdir, writeFile} from 'node:fs/promises';
import {chromium} from 'playwright';
const base=process.env.BASE_URL || 'http://127.0.0.1:3000';
assert.equal(new URL(base).hostname,'127.0.0.1');assert.equal(process.env.MIS_SIM_DISPOSABLE,'1');
const out=process.env.ARTIFACT_DIR || '/tmp/mis-sim-readiness-controls';await mkdir(out,{recursive:true});
const b=await chromium.launch();const p=await b.newPage({viewport:{width:1280,height:1000}});p.setDefaultTimeout(60000);
const errors=[],checks=[];let completed=false;
p.on('pageerror',e=>errors.push(e.message));p.on('console',m=>{if(m.type()==='error')errors.push(m.text());});p.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`);});
async function save(section,button){const response=p.waitForResponse(r=>r.url().endsWith(section)&&r.request().method()==='PATCH');await p.getByRole('button',{name:button,exact:true}).click();const r=await response;assert.equal(r.status(),200,await r.text());return r.json();}
function pass(s){checks.push(s);console.log(`PASS ${s}`);}
try {
 await p.goto(`${base}/login`);await p.getByLabel('Student ID').fill('M2-205');await p.getByLabel('Password',{exact:true}).fill('StudentPass!2026');await p.getByRole('button',{name:'Sign in',exact:true}).click();await p.waitForURL(`${base}/`);
 const token=await p.evaluate(()=>sessionStorage.getItem('mis_sim.access_token'));const headers={Authorization:`Bearer ${token}`};
 const get=async path=>{const r=await p.request.get(`${base}/api${path}`,{headers});assert.equal(r.status(),200);return r.json();};
 const me=await get('/auth/me');const prefix=`/instances/${me.instance_id}`;
 await p.goto(`${base}/strategy`);await save('/controls/strategy','Save strategy');
 await p.goto(`${base}/rollout`);await p.getByRole('slider').first().focus();await p.keyboard.press('End');await save('/rollout','Save Changes');
 await p.getByRole('tab',{name:'Ownership',exact:true}).click();await p.locator('.detail-table tbody select').first().selectOption('finance');
 const own=await save('/controls/governance','Save ownership decisions');assert.ok(own.team.selected_commands.some(c=>c.op==='declare_strategy'));const assign=own.team.selected_commands.find(c=>c.op==='assign'&&c.owner==='finance');assert.ok(assign);
 await p.getByRole('tab').first().click();await save('/rollout','Save Changes');pass('Rollout and Ownership share the current revision and retain strategy');
 await p.goto(`${base}/strategy`);const strategy=await save('/controls/strategy','Save strategy');assert.ok(strategy.team.selected_commands.some(c=>c.op==='assign'&&c.capability===assign.capability&&c.owner==='finance'));pass('Strategy save preserves pending ownership');
 await p.goto(`${base}/infrastructure`);await p.getByRole('tab',{name:'Security & data policies',exact:true}).click();
 const policy=p.getByLabel('Who can access customer records?');const options=await policy.locator('option').evaluateAll(els=>els.map(e=>e.value).filter(Boolean));await policy.selectOption(options.at(-1));await save('/controls/security','Save data policies');
 await p.getByRole('tab',{name:'People',exact:true}).click();const hire=p.getByLabel('Hiring option');const hireValue=await hire.locator('option').nth(1).getAttribute('value');await hire.selectOption(hireValue);const people=await save('/controls/people','Save people decisions');assert.ok(people.team.selected_commands.some(c=>c.op==='communicate'));pass('People is reachable and hiring preserves rollout communication');
 await p.getByRole('tab',{name:'Security & data policies',exact:true}).click();assert.equal(await policy.inputValue(),options.at(-1));await save('/controls/security','Save data policies');pass('Security and People saves share revisions and retain draft policy selections');
 await p.reload();await p.getByRole('tab',{name:'Security & data policies',exact:true}).click();assert.equal(await policy.inputValue(),options.at(-1));await p.screenshot({path:`${out}/security.png`,fullPage:true});
 await p.goto(`${base}/rollout`);await p.getByRole('tab',{name:'Ownership',exact:true}).click();assert.equal(await p.locator('.detail-table tbody select').first().inputValue(),'finance');pass('Policy and ownership choices survive page reload');
 await p.setViewportSize({width:720,height:1000});await p.screenshot({path:`${out}/ownership-720.png`,fullPage:true});assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth-innerWidth)<=1);assert.deepEqual(errors,[]);completed=true;
}finally{await writeFile(`${out}/results.json`,JSON.stringify({status:completed?'pass':'fail',checks,errors},null,2));await b.close();}
