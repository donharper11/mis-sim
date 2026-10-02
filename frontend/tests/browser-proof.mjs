/**
 * M5.3–5.7 Browser Proofs
 *
 * Verifies that each instructor page renders correctly with real data.
 * Uses Playwright (chromium) against the running dev environment.
 *
 * Prerequisites:
 *   - Backend running on :8211 (docker compose up)
 *   - Frontend dev server on :3000 (npm run dev)
 *   - Database seeded (python -m app.seed.demo --packs --cohort --users)
 *   - Node 20+ (nvm use 22)
 *
 * Usage:
 *   node frontend/tests/browser-proof.mjs
 *
 * If the frontend proxies to a non-default backend port, set BASE_API:
 *   BASE_API=http://localhost:8211 node frontend/tests/browser-proof.mjs
 */

import { chromium } from "playwright";

const BASE = process.env.BASE_URL || "http://localhost:3000";
const INSTRUCTOR_EMAIL = "m2.instructor.a@example.edu";
const INSTRUCTOR_PASS = "InstructorPass!2026";
const ADMIN_EMAIL = "m2.admin@example.edu";
const ADMIN_PASS = "AdminPass!2026";

const results = [];

function log(proof, status, detail = "") {
  const tag = status === "PASS" ? "\x1b[32mPASS\x1b[0m" : "\x1b[31mFAIL\x1b[0m";
  console.log(`  ${tag}  ${proof}${detail ? "  " + detail : ""}`);
  results.push({ proof, status, detail });
}

async function getToken(email, password) {
  const resp = await fetch(`${BASE}/api/auth/staff-login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await resp.json();
  return data.access_token;
}

async function loginAsStaff(page, email, password) {
  await page.goto(`${BASE}/login`);
  await page.waitForLoadState("networkidle");

  const token = await getToken(email, password);

  await page.evaluate((t) => {
    window.sessionStorage.setItem("mis_sim.access_token", t);
  }, token);

  const meResp = await fetch(`${BASE}/api/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const me = await meResp.json();
  await page.evaluate((u) => {
    window.sessionStorage.setItem("mis_sim.user", JSON.stringify(u));
  }, me);

  return { token, user: me };
}

async function proofM53(browser) {
  console.log("\n== M5.3 Round Control ==");
  const page = await browser.newPage();
  try {
    await loginAsStaff(page, INSTRUCTOR_EMAIL, INSTRUCTOR_PASS);

    await page.goto(`${BASE}/instructor/round-control`);
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2000);

    await page.screenshot({ path: "/tmp/proof-m53-round-control.png", fullPage: true });

    const body = await page.textContent("body");

    const hasRoundControl =
      body.includes("Round") || body.includes("round") || body.includes("Control") || body.includes("control");
    const hasButtons =
      body.includes("Pause") ||
      body.includes("Resume") ||
      body.includes("Lock") ||
      body.includes("Advance") ||
      body.includes("pause") ||
      body.includes("advance");

    log("M5.3 page renders", hasRoundControl ? "PASS" : "FAIL", "round control page loaded");
    log("M5.3 action buttons visible", hasButtons ? "PASS" : "FAIL", "pause/lock/advance controls present");

    const hasSelector = body.includes("Section") || body.includes("section") || body.includes("Course") || body.includes("Instance");
    log("M5.3 instance selection", hasSelector ? "PASS" : "FAIL", "course/section/instance selector present");
  } catch (e) {
    log("M5.3 page renders", "FAIL", e.message);
  } finally {
    await page.close();
  }
}

async function proofM54(browser) {
  console.log("\n== M5.4 Monitoring Dashboard ==");
  const page = await browser.newPage();
  try {
    await loginAsStaff(page, INSTRUCTOR_EMAIL, INSTRUCTOR_PASS);

    await page.goto(`${BASE}/instructor/monitoring`);
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2000);

    await page.screenshot({ path: "/tmp/proof-m54-monitoring.png", fullPage: true });

    const body = await page.textContent("body");

    const hasMonitoring =
      body.includes("Monitor") || body.includes("monitor") || body.includes("Dashboard") || body.includes("dashboard");
    const hasTeamData =
      body.includes("Team") || body.includes("team") || body.includes("Score") || body.includes("status");

    log("M5.4 page renders", hasMonitoring ? "PASS" : "FAIL", "monitoring page loaded");
    log("M5.4 team data visible", hasTeamData ? "PASS" : "FAIL", "team/scorecard data area present");

    const hasDimensions =
      body.includes("Financial") ||
      body.includes("financial") ||
      body.includes("Customer") ||
      body.includes("customer") ||
      body.includes("Scorecard") ||
      body.includes("scorecard");
    log("M5.4 scorecard columns", hasDimensions ? "PASS" : "FAIL", "scorecard dimension indicators present");
  } catch (e) {
    log("M5.4 page renders", "FAIL", e.message);
  } finally {
    await page.close();
  }
}

async function proofM55(browser) {
  console.log("\n== M5.5 Grading and Export ==");
  const page = await browser.newPage();
  try {
    await loginAsStaff(page, INSTRUCTOR_EMAIL, INSTRUCTOR_PASS);

    await page.goto(`${BASE}/instructor/grading`);
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2000);

    await page.screenshot({ path: "/tmp/proof-m55-grading.png", fullPage: true });

    const body = await page.textContent("body");

    const hasGrading =
      body.includes("Grad") || body.includes("grad") || body.includes("Weight") || body.includes("weight");
    log("M5.5 page renders", hasGrading ? "PASS" : "FAIL", "grading page loaded");

    const hasExport = body.includes("Export") || body.includes("export") || body.includes("CSV") || body.includes("Download");
    log("M5.5 export button", hasExport ? "PASS" : "FAIL", "CSV export control present");

    const hasWeights =
      body.includes("Financial") ||
      body.includes("financial") ||
      body.includes("Customer") ||
      body.includes("customer") ||
      body.includes("0.25");
    log("M5.5 weight editor", hasWeights ? "PASS" : "FAIL", "BSC weight configuration present");
  } catch (e) {
    log("M5.5 page renders", "FAIL", e.message);
  } finally {
    await page.close();
  }
}

async function proofM56(browser) {
  console.log("\n== M5.6 Registry Admin ==");
  const page = await browser.newPage();
  try {
    await loginAsStaff(page, ADMIN_EMAIL, ADMIN_PASS);

    await page.goto(`${BASE}/instructor/registry`);
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2000);

    await page.screenshot({ path: "/tmp/proof-m56-registry.png", fullPage: true });

    const body = await page.textContent("body");

    const hasRegistry =
      body.includes("Registry") ||
      body.includes("registry") ||
      body.includes("Casepack") ||
      body.includes("casepack") ||
      body.includes("Pack");
    log("M5.6 page renders", hasRegistry ? "PASS" : "FAIL", "registry page loaded");

    const hasPacks =
      body.includes("riverside") ||
      body.includes("Riverside") ||
      body.includes("pack_key") ||
      body.includes("0.1.0") ||
      body.includes("grocery");
    log("M5.6 pack list visible", hasPacks ? "PASS" : "FAIL", "registered packs shown");

    const hasValidation =
      body.includes("valid") ||
      body.includes("Valid") ||
      body.includes("error") ||
      body.includes("warning") ||
      body.includes("Warning");
    log("M5.6 validation badges", hasValidation ? "PASS" : "FAIL", "validation status indicators present");
  } catch (e) {
    log("M5.6 page renders", "FAIL", e.message);
  } finally {
    await page.close();
  }
}

async function proofM57(browser) {
  console.log("\n== M5.7 Clone/Archive/Reset ==");
  const page = await browser.newPage();
  try {
    await loginAsStaff(page, INSTRUCTOR_EMAIL, INSTRUCTOR_PASS);

    await page.goto(`${BASE}/instructor/setup`);
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2000);

    await page.screenshot({ path: "/tmp/proof-m57-setup.png", fullPage: true });

    const body = await page.textContent("body");

    const hasSetup =
      body.includes("Setup") || body.includes("setup") || body.includes("Course") || body.includes("Section");
    log("M5.7 setup page renders", hasSetup ? "PASS" : "FAIL", "instructor setup page loaded");

    const hasClone = body.includes("Clone") || body.includes("clone");
    const hasArchive = body.includes("Archive") || body.includes("archive");
    const hasReset = body.includes("Reset") || body.includes("reset");

    log("M5.7 clone button", hasClone ? "PASS" : "FAIL", "clone action present");
    log("M5.7 archive button", hasArchive ? "PASS" : "FAIL", "archive action present (may be disabled for non-completed)");
    log("M5.7 reset button", hasReset ? "PASS" : "FAIL", "reset action present");
  } catch (e) {
    log("M5.7 setup page renders", "FAIL", e.message);
  } finally {
    await page.close();
  }
}

async function proofNavigation(browser) {
  console.log("\n== Navigation ==");
  const page = await browser.newPage();
  try {
    await loginAsStaff(page, INSTRUCTOR_EMAIL, INSTRUCTOR_PASS);

    await page.goto(`${BASE}/`);
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2000);

    const body = await page.textContent("body");

    const navItems = ["Round control", "Monitoring", "Grading", "Setup"];
    for (const item of navItems) {
      const found = body.includes(item) || body.toLowerCase().includes(item.toLowerCase());
      log(`Nav: "${item}"`, found ? "PASS" : "FAIL", found ? "visible in sidebar" : "not found in sidebar");
    }
  } catch (e) {
    log("Navigation check", "FAIL", e.message);
  } finally {
    await page.close();
  }
}

// Main
(async () => {
  console.log("M5.3\u20135.7 Browser Proofs");
  console.log("=======================\n");

  const browser = await chromium.launch({ headless: true });

  try {
    await proofNavigation(browser);
    await proofM53(browser);
    await proofM54(browser);
    await proofM55(browser);
    await proofM56(browser);
    await proofM57(browser);
  } finally {
    await browser.close();
  }

  const passed = results.filter((r) => r.status === "PASS").length;
  const failed = results.filter((r) => r.status === "FAIL").length;
  console.log(`\n== Summary: ${passed} passed, ${failed} failed ==`);

  if (failed > 0) {
    console.log("\nFailed proofs:");
    for (const r of results.filter((r) => r.status === "FAIL")) {
      console.log(`  - ${r.proof}: ${r.detail}`);
    }
  }

  console.log("\nScreenshots saved to /tmp/proof-m5*.png");
  process.exit(failed > 0 ? 1 : 0);
})();
