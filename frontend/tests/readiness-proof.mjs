/** Mutates only a fresh local readiness cohort. See docs/readiness-runbook.md. */
import assert from 'node:assert/strict';
import {mkdir, writeFile} from 'node:fs/promises';
import {chromium} from 'playwright';

const base = process.env.BASE_URL || 'http://127.0.0.1:3000';
assert.equal(new URL(base).hostname, '127.0.0.1', 'Readiness proof requires an explicit local host');
assert.equal(process.env.MIS_SIM_DISPOSABLE, '1', 'Set MIS_SIM_DISPOSABLE=1 only for a disposable seeded cohort');
const artifacts = process.env.ARTIFACT_DIR || '/tmp/mis-sim-readiness-browser';
await mkdir(artifacts, {recursive:true});
const browser = await chromium.launch();
const failures = [], checks = [];
let completed = false;
function record(message) { checks.push(message); console.log(`PASS ${message}`); }
function observe(page) {
  page.on('pageerror',e=>failures.push(e.message));
  page.on('console',m=>{if(m.type()==='error') failures.push(m.text());});
  page.on('response',r=>{if(r.status()>=400) failures.push(`${r.status()} ${r.url()}`);});
  page.on('requestfailed',r=>{if(r.failure()?.errorText !== 'net::ERR_ABORTED') failures.push(`${r.url()} ${r.failure()?.errorText}`);});
}
async function login(page, staff=false) {
  await page.goto(`${base}/login`);
  if(staff) await page.getByRole('button',{name:'Staff',exact:true}).click();
  await page.getByLabel(staff?'Email':'Student ID',{exact:true}).fill(staff?'m2.instructor.a@example.edu':'M2-101');
  await page.getByLabel('Password',{exact:true}).fill(staff?'InstructorPass!2026':'StudentPass!2026');
  await page.getByRole('button',{name:'Sign in',exact:true}).click();
  await page.waitForURL(`${base}/`);
  await page.locator('.product-shell').waitFor();
}
async function visit(page, path) {
  await page.goto(`${base}${path}`);
  await page.locator('.product-shell').waitFor();
  await page.locator('.product-shell__content').waitFor();
}
async function api(page, path) {
  const token=await page.evaluate(()=>sessionStorage.getItem('mis_sim.access_token'));
  const r=await page.request.get(`${base}/api${path}`,{headers:{Authorization:`Bearer ${token}`}});
  assert.equal(r.status(),200,await r.text());return r.json();
}
const student = await browser.newPage({viewport:{width:1440,height:1000}});
const staff = await browser.newPage({viewport:{width:1440,height:1000}});
observe(student); observe(staff);
try {
  await login(student);
  const me=await api(student,'/auth/me'); const prefix=`/instances/${me.instance_id}`;
  const initial=await api(student,`${prefix}/rollout`);
  assert.equal(initial.team.current_round,1,'Requires a fresh round-one seed');
  record('Student browser login and scoped API canary');
  for(const width of [1440,1280,1024,720]) {
    await student.setViewportSize({width,height:1000});
    for(const route of ['/','/strategy','/infrastructure','/applications','/rollout','/review','/debrief','/challenges']) {
      await visit(student,route);
      const overflow=await student.evaluate(()=>document.documentElement.scrollWidth-innerWidth);
      assert.ok(overflow<=1,`${route} overflows ${overflow}px at ${width}`);
    }
    await visit(student,'/rollout');
    await student.screenshot({path:`${artifacts}/rollout-${width}.png`,fullPage:true});
    record(`Eight student routes at ${width}px, no page overflow`);
  }
  await student.setViewportSize({width:1440,height:1000});
  await visit(student,'/rollout');
  const tabs=student.getByRole('tab');
  for(const index of [0,1]) {
    await tabs.nth(index).click();
    // A real edit, then save; choice survives reload and preserves another asset.
    await student.getByRole('slider').first().focus();
    await student.keyboard.press('End');
    const response=student.waitForResponse(r=>r.url().endsWith('/rollout') && r.request().method()==='PATCH');
    await student.getByRole('button',{name:'Save Changes',exact:true}).click();
    const saved=await response; assert.equal(saved.status(),200,await saved.text());
  }
  const saved=await api(student,`${prefix}/rollout`);
  assert.ok(saved.team.selected_commands.filter(c=>c.op==='train').length>=2);
  await visit(student,'/rollout');
  assert.equal(await student.getByRole('slider').first().getAttribute('aria-valuenow'),'100');
  record('Two application rollout saves persist without erasing one another');
  await visit(student,'/review');
  const review=await api(student,`${prefix}/review`);
  const dashboard=await api(student,`${prefix}/dashboard`);
  assert.equal(dashboard.teams[0].capital_remaining,review.team.capital_remaining);
  record('Headline capital reconciles to current-round review');
  const locked=student.waitForResponse(r=>r.url().endsWith('/review/lock'));
  await student.getByRole('button',{name:'Lock round',exact:true}).click();
  assert.equal((await locked).status(),200);
  await visit(student,'/rollout');
  assert.equal(await student.getByRole('button',{name:'Save Changes',exact:true}).isDisabled(),true);
  record('Review lock makes rollout read-only');
  await login(staff,true);
  for(const route of ['/instructor/setup','/instructor/round-control','/instructor/monitoring','/instructor/grading']) {
    await visit(staff,route);
    await staff.screenshot({path:`${artifacts}/${route.split('/').at(-1)}.png`,fullPage:true});
  }
  record('Instructor login and four authenticated workspaces');
  for(let round=1;round<=6;round++) {
    await visit(staff,'/instructor/round-control');
    const response=staff.waitForResponse(r=>r.url().endsWith('/round-control/advance'));
    await staff.getByRole('button',{name:'Advance round',exact:true}).click();
    const advanced=await response;assert.equal(advanced.status(),200,await advanced.text());
    assert.equal((await advanced.json()).round,round);
    await visit(student,'/debrief');
    const report=await api(student,`${prefix}/debrief`);
    assert.equal(report.team.latest_round,round);
    assert.equal(report.team.rounds.length,round);
    record(`Instructor advanced round ${round}; student reads persisted result`);
  }
  await student.screenshot({path:`${artifacts}/debrief-round-6.png`,fullPage:true});
  const download=student.waitForEvent('download');
  await student.getByRole('button',{name:'Download report',exact:true}).click();
  await (await download).saveAs(`${artifacts}/debrief.txt`);
  record('Completed six-round report download');
  assert.deepEqual(failures,[],'Browser diagnostics must be clean');
  record('Zero console/page/network errors');
  completed = true;
} finally {
  await writeFile(`${artifacts}/results.json`,JSON.stringify({status: completed ? "pass" : "fail", checks,failures},null,2));
  await browser.close();
}
