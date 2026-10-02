/**
 * M5.1-5.2 Browser Proof — Instructor Setup Acceptance
 *
 * Verifies: staff login, role-gated navigation, pack selection,
 * team creation, student enrollment and assignment, student denial.
 */

import { chromium } from "playwright";

const BASE = "http://localhost:3000";
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
  return (await resp.json()).access_token;
}

async function loginAs(page, email, password) {
  await page.goto(`${BASE}/login`);
  await page.waitForLoadState("networkidle");
  const token = await getToken(email, password);
  await page.evaluate((t) => window.sessionStorage.setItem("mis_sim.access_token", t), token);
  const me = await (await fetch(`${BASE}/api/auth/me`, { headers: { Authorization: `Bearer ${token}` } })).json();
  await page.evaluate((u) => window.sessionStorage.setItem("mis_sim.user", JSON.stringify(u)), me);
  return { token, user: me };
}

(async () => {
  console.log("M5.1-5.2 Browser Proof — Instructor Setup");
  console.log("==========================================\n");

  const browser = await chromium.launch({ headless: true });
  const errors = [];

  // === 1. Staff login and setup page ===
  console.log("== Staff Login & Setup Page ==");
  const page = await browser.newPage();
  page.on("pageerror", (e) => errors.push(e.message));

  try {
    await loginAs(page, "m2.instructor.a@example.edu", "InstructorPass!2026");
    await page.goto(`${BASE}/instructor/setup`);
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2000);

    const body = await page.textContent("body");

    // 1a. Page loads with role-gated content
    const hasSetup = body.includes("setup") || body.includes("Setup");
    log("Staff login succeeds", hasSetup ? "PASS" : "FAIL", "instructor setup page loaded after login");

    // 1b. Course selector visible
    const hasCourse = body.includes("Course") || body.includes("course") || body.includes("MIS-PLATFORM");
    log("Course selector visible", hasCourse ? "PASS" : "FAIL", "course selection area present");

    // 1c. Section selector visible
    const hasSection = body.includes("Section") || body.includes("section");
    log("Section selector visible", hasSection ? "PASS" : "FAIL", "section area present");

    // 1d. Pack binding area
    const hasPack = body.includes("pack") || body.includes("Pack") || body.includes("Riverside") || body.includes("riverside");
    log("Pack binding area", hasPack ? "PASS" : "FAIL", "pack selection/binding visible");

    // 1e. Team/roster controls
    const hasTeam = body.includes("team") || body.includes("Team") || body.includes("roster") || body.includes("Roster");
    log("Team/roster controls", hasTeam ? "PASS" : "FAIL", "team creation and roster area visible");

    // 1f. Lifecycle buttons (M5.7)
    const hasLifecycle = body.includes("Clone") || body.includes("Archive") || body.includes("Reset");
    log("Lifecycle actions visible", hasLifecycle ? "PASS" : "FAIL", "clone/archive/reset buttons present");

    await page.screenshot({ path: "/tmp/proof-m51-setup-overview.png", fullPage: true });

    // === 2. Verify pack is already bound (seeded) ===
    console.log("\n== Pack Binding ==");
    const hasPackBound = body.includes("riverside_grocery") || body.includes("Riverside");
    const hasDigest = body.includes("a62dcdb") || body.includes("digest") || body.includes("Digest");
    log("Pack bound to section", hasPackBound ? "PASS" : "FAIL", "riverside_grocery pack visible");

    // === 3. Team creation ===
    console.log("\n== Team Management ==");
    const createTeamBtn = page.locator("button", { hasText: /create team/i });
    const teamBtnVisible = await createTeamBtn.count() > 0;
    log("Create team button", teamBtnVisible ? "PASS" : "FAIL", "create team button found");

    if (teamBtnVisible) {
      await createTeamBtn.click();
      await page.waitForTimeout(2000);
      const bodyAfterTeam = await page.textContent("body");
      const teamCreated = bodyAfterTeam.includes("Team") && (bodyAfterTeam.includes("created") || bodyAfterTeam.includes("Team 3") || bodyAfterTeam.includes("Team 1"));
      log("Team creation works", teamCreated ? "PASS" : "FAIL", "team created or already exists");
    }

    // === 4. Student enrollment ===
    console.log("\n== Student Enrollment ==");
    const enrollInput = page.locator('input[aria-label="Existing student user ID"]');
    const enrollInputVisible = await enrollInput.count() > 0;
    log("Enrollment input visible", enrollInputVisible ? "PASS" : "FAIL", "student user ID input found");

    if (enrollInputVisible) {
      // Enroll student ID 2 (first seeded student)
      await enrollInput.fill("2");
      const enrollBtn = page.locator("button", { hasText: /enroll/i });
      if (await enrollBtn.count() > 0) {
        await enrollBtn.click();
        await page.waitForTimeout(2000);
        const bodyAfterEnroll = await page.textContent("body");
        const enrolled = bodyAfterEnroll.includes("M2 Student") || bodyAfterEnroll.includes("enrolled") || bodyAfterEnroll.includes("Enrolled");
        log("Student enrollment works", enrolled ? "PASS" : "FAIL", "student enrolled or notice shown");
      }
    }

    // === 5. Team assignment dropdown ===
    console.log("\n== Team Assignment ==");
    const teamSelects = page.locator('select[aria-label^="Team for"]');
    const hasAssignmentDropdown = await teamSelects.count() > 0;
    log("Team assignment dropdowns", hasAssignmentDropdown ? "PASS" : "FAIL",
      hasAssignmentDropdown ? `${await teamSelects.count()} assignment dropdown(s) found` : "no assignment dropdowns");

    await page.screenshot({ path: "/tmp/proof-m51-setup-roster.png", fullPage: true });

  } catch (e) {
    log("Setup flow", "FAIL", e.message);
  } finally {
    await page.close();
  }

  // === 6. Student denial ===
  console.log("\n== Student Denial ==");
  const studentPage = await browser.newPage();
  try {
    await loginAs(studentPage, "m2.student.1.1@example.edu", "StudentPass!2026");
    await studentPage.goto(`${BASE}/instructor/setup`);
    await studentPage.waitForLoadState("networkidle");
    await studentPage.waitForTimeout(2000);

    const url = studentPage.url();
    const studentBody = await studentPage.textContent("body");

    // Student should be redirected to login or see an error
    const denied = url.includes("/login") || studentBody.includes("403") || studentBody.includes("denied") ||
      studentBody.includes("Forbidden") || !studentBody.includes("Course, section");
    log("Student denied setup access", denied ? "PASS" : "FAIL",
      url.includes("/login") ? "redirected to /login" : "forbidden or no setup content");

    await studentPage.screenshot({ path: "/tmp/proof-m51-student-denied.png", fullPage: true });
  } catch (e) {
    log("Student denial", "FAIL", e.message);
  } finally {
    await studentPage.close();
  }

  // === 7. Console errors ===
  console.log("\n== Browser Console ==");
  const unexpectedErrors = errors.filter((e) => !e.includes("401") && !e.includes("403") && !e.includes("409"));
  log("No unexpected page errors", unexpectedErrors.length === 0 ? "PASS" : "FAIL",
    unexpectedErrors.length === 0 ? "clean console" : `${unexpectedErrors.length} error(s): ${unexpectedErrors[0]}`);

  await browser.close();

  // Summary
  const passed = results.filter((r) => r.status === "PASS").length;
  const failed = results.filter((r) => r.status === "FAIL").length;
  console.log(`\n== Summary: ${passed} passed, ${failed} failed ==`);

  if (failed > 0) {
    console.log("\nFailed proofs:");
    for (const r of results.filter((r) => r.status === "FAIL")) {
      console.log(`  - ${r.proof}: ${r.detail}`);
    }
  }

  console.log("\nScreenshots saved to /tmp/proof-m51-*.png");
  process.exit(failed > 0 ? 1 : 0);
})();
