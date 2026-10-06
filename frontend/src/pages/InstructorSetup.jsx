import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import AppShell from "../components/AppShell.jsx";
import {
  apiClient,
  getCourseSetup,
  getCurrentUser,
  getInstanceTeams,
  getSectionRoster,
  listCasepacks,
  listInstructorCourses,
  clearAccessToken
} from "../api/client.js";

function requestError(error) {
  const detail = error.response?.data?.detail;
  return typeof detail === "string" ? detail : "Check the selected settings and try again.";
}

export default function InstructorSetup() {
  const navigate = useNavigate();
  const [state, setState] = useState({ loading: true, me: null, courses: [], packs: [], setup: null, courseId: null, sectionId: null, roster: [], teams: [], error: "", notice: "" });
  const [newCourse, setNewCourse] = useState({ course_code: "", course_name: "", academic_year: "2026", semester: "A" });
  const [newSection, setNewSection] = useState({ section_code: "", section_name: "" });
  const [packKey, setPackKey] = useState("");
  const [studentId, setStudentId] = useState("");
  const loadSerial = useRef(0);
  const [start, setStart] = useState({ readiness: null, choices: {}, confirm: false, pending: false });

  // M5.7 lifecycle modal state
  const [cloneModal, setCloneModal] = useState({ open: false, sectionId: null, code: "", name: "" });
  const [archiveModal, setArchiveModal] = useState({ open: false, instanceId: null, confirmId: "" });
  const [resetModal, setResetModal] = useState({ open: false, instanceId: null, confirmId: "" });

  const load = useCallback(async (courseId = null, sectionId = null) => {
    const serial = ++loadSerial.current;
    try {
      const [meResponse, coursesResponse, packsResponse] = await Promise.all([getCurrentUser(), listInstructorCourses(), listCasepacks()]);
      const courses = coursesResponse.data;
      const selectedCourseId = courseId || courses[0]?.id || null;
      const setupResponse = selectedCourseId ? await getCourseSetup(selectedCourseId) : { data: null };
      const setup = setupResponse.data;
      const selectedSectionId = sectionId || setup?.sections?.[0]?.id || null;
      const selectedSection = setup?.sections?.find((item) => item.id === selectedSectionId);
      const rosterResponse = selectedSectionId ? await getSectionRoster(selectedSectionId) : { data: [] };
      const teamsResponse = selectedSection?.instance ? await getInstanceTeams(selectedSection.instance.instance_id) : { data: [] };
      const readiness = selectedSection?.instance ? (await apiClient.get(`/instructor/instances/${selectedSection.instance.instance_id}/start-readiness`)).data : null;
      if (serial !== loadSerial.current) return;
      setStart((previous) => ({ ...previous, readiness, choices: previous.readiness?.instance_id === readiness?.instance_id ? previous.choices : {}, confirm: false }));
      setState((previous) => ({ ...previous, loading: false, me: meResponse.data, courses, packs: packsResponse.data, setup, courseId: selectedCourseId, sectionId: selectedSectionId, roster: rosterResponse.data, teams: teamsResponse.data, error: "" }));
      if (packsResponse.data[0]) setPackKey((previous) => previous || `${packsResponse.data[0].pack_key}@${packsResponse.data[0].pack_version}`);
    } catch (error) {
      if (serial !== loadSerial.current) return;
      if ([401, 403].includes(error.response?.status)) {
        clearAccessToken();
        navigate("/login", { replace: true });
        return;
      }
      setState((previous) => ({ ...previous, loading: false, error: requestError(error) }));
    }
  }, [navigate]);

  useEffect(() => { load(); }, [load]);

  const selectedSection = useMemo(() => state.setup?.sections?.find((item) => item.id === state.sectionId), [state.setup, state.sectionId]);
  const selectedPack = state.packs.find((pack) => `${pack.pack_key}@${pack.pack_version}` === packKey);

  async function perform(action, success) {
    try {
      await action();
      setState((previous) => ({ ...previous, notice: success, error: "" }));
      await load(state.courseId, state.sectionId);
    } catch (error) {
      setState((previous) => ({ ...previous, error: requestError(error), notice: "" }));
    }
  }

  async function handleStart() {
    if (start.pending || !start.readiness?.ready) return;
    const readiness = start.readiness;
    setStart((previous) => ({ ...previous, pending: true }));
    try {
      await apiClient.post(`/instructor/instances/${readiness.instance_id}/start`, {
        confirm_instance_id: readiness.instance_id,
        expected_pack_digest: readiness.pack_digest,
        team_strategies: readiness.teams.map((team) => ({ team_id: team.team_id, strategy_key: start.choices[team.team_id] }))
      });
      setStart((previous) => ({ ...previous, confirm: false }));
      setState((previous) => ({ ...previous, notice: "Simulation started. Round 1 is open.", error: "" }));
      await load(state.courseId, state.sectionId);
    } catch (error) {
      setState((previous) => ({ ...previous, error: requestError(error), notice: "" }));
      setStart((previous) => ({ ...previous, confirm: false }));
    } finally {
      setStart((previous) => ({ ...previous, pending: false }));
    }
  }

  async function createCourse(event) {
    event.preventDefault();
    await perform(() => apiClient.post("/courses", newCourse), "Course created.");
    setNewCourse({ course_code: "", course_name: "", academic_year: "2026", semester: "A" });
  }

  async function createSection(event) {
    event.preventDefault();
    if (!state.courseId) return;
    await perform(() => apiClient.post(`/courses/${state.courseId}/sections`, { ...newSection, max_teams: 8, team_size_min: 2, team_size_max: 6 }), "Section created.");
    setNewSection({ section_code: "", section_name: "" });
  }

  async function bindPack() {
    if (!selectedSection || !selectedPack) return;
    await perform(() => apiClient.post(`/sections/${selectedSection.id}/instance`, { pack_key: selectedPack.pack_key, pack_version: selectedPack.pack_version, total_rounds: selectedPack.rounds }), "Pack bound and pinned to this setup.");
  }

  async function createTeam() {
    if (!selectedSection?.instance) return;
    await perform(() => apiClient.post(`/instances/${selectedSection.instance.instance_id}/teams`, { name: `Team ${state.teams.length + 1}` }), "Team created.");
  }

  async function enrollStudent(event) {
    event.preventDefault();
    if (!selectedSection || !studentId) return;
    await perform(() => apiClient.post(`/sections/${selectedSection.id}/enrollments`, { user_id: Number(studentId), role: "student" }), "Existing student identity enrolled.");
    setStudentId("");
  }

  async function assign(enrollmentId, teamId) {
    await perform(() => apiClient.patch(`/sections/${selectedSection.id}/enrollments/${enrollmentId}`, { team_id: teamId ? Number(teamId) : null }), "Roster assignment saved.");
  }

  // M5.7 lifecycle actions
  async function handleClone() {
    const body = {};
    if (cloneModal.code.trim()) body.section_code = cloneModal.code.trim();
    if (cloneModal.name.trim()) body.section_name = cloneModal.name.trim();
    setCloneModal({ open: false, sectionId: null, code: "", name: "" });
    await perform(() => apiClient.post(`/instructor/sections/${cloneModal.sectionId}/clone`, body), "Section cloned successfully.");
  }

  async function handleArchive() {
    const iid = archiveModal.instanceId;
    setArchiveModal({ open: false, instanceId: null, confirmId: "" });
    await perform(() => apiClient.post(`/instructor/instances/${iid}/archive`, { confirm_instance_id: iid }), "Instance archived.");
  }

  async function handleReset() {
    const iid = resetModal.instanceId;
    setResetModal({ open: false, instanceId: null, confirmId: "" });
    await perform(() => apiClient.post(`/instructor/instances/${iid}/reset`, { confirm_instance_id: iid }), "Instance reset. All runtime state cleared.");
  }

  function selectCourse(event) {
    const courseId = Number(event.target.value);
    setState((previous) => ({ ...previous, courseId, sectionId: null, setup: null, roster: [], teams: [], error: "" }));
    load(courseId, null);
  }

  function selectSection(event) {
    const sectionId = Number(event.target.value);
    setState((previous) => ({ ...previous, sectionId, setup: null, roster: [], teams: [], error: "" }));
    load(state.courseId, sectionId);
  }

  if (state.loading) return <main className="app-shell plain-state"><p>Loading instructor setup…</p></main>;
  return <AppShell me={state.me} activePath="/instructor/setup" pageTitle="Instructor setup">
    <div className="instructor-workspace">
      <fieldset disabled={start.pending} style={{ border: 0, margin: 0, padding: 0, minWidth: 0 }}>
      <header className="page-header">
        <p className="eyebrow">M5.1 / M5.2</p>
        <h2>Course, section, and roster setup</h2>
        <p className="page-intro">Use registered packs and existing student identities to prepare a setup-state section. Account provisioning and CSV import are separate work.</p>
      </header>
      {state.error && <p className="workspace-message workspace-message--error" role="alert">{state.error}</p>}
      {state.notice && <p className="workspace-message workspace-message--ok" role="status">{state.notice}</p>}
      <section className="setup-card" aria-labelledby="course-heading">
        <h3 id="course-heading">Course</h3>
        <label>Selected course<select value={state.courseId || ""} onChange={selectCourse}><option value="">Choose a course</option>{state.courses.map((course) => <option key={course.id} value={course.id}>{course.course_code} — {course.course_name}</option>)}</select></label>
        <form className="setup-inline-form" onSubmit={createCourse}><input aria-label="Course code" placeholder="Course code" value={newCourse.course_code} onChange={(event) => setNewCourse({ ...newCourse, course_code: event.target.value })} required /><input aria-label="Course name" placeholder="Course name" value={newCourse.course_name} onChange={(event) => setNewCourse({ ...newCourse, course_name: event.target.value })} required /><button type="submit">Create course</button></form>
      </section>
      {state.setup && <>
        <section className="setup-card" aria-labelledby="section-heading">
          <h3 id="section-heading">Section</h3>
          <label>Selected section<select value={state.sectionId || ""} onChange={selectSection}>{state.setup.sections.map((section) => <option key={section.id} value={section.id}>{section.section_code} — {section.section_name}</option>)}</select></label>
          <form className="setup-inline-form" onSubmit={createSection}><input aria-label="Section code" placeholder="Section code" value={newSection.section_code} onChange={(event) => setNewSection({ ...newSection, section_code: event.target.value })} required /><input aria-label="Section name" placeholder="Section name" value={newSection.section_name} onChange={(event) => setNewSection({ ...newSection, section_name: event.target.value })} required /><button type="submit">Create section</button></form>
        </section>
        {selectedSection && <>
          <section className="setup-card" aria-labelledby="pack-heading">
            <h3 id="pack-heading">Registered pack</h3>
            <p className="muted-copy">A pack binding is digest-pinned and can only be created before round 1.</p>
            {selectedSection.instance ? <dl className="setup-facts"><div><dt>Pack</dt><dd>{selectedSection.instance.pack_key} {selectedSection.instance.pack_version}</dd></div><div><dt>Digest</dt><dd className="mono-copy">{selectedSection.instance.pack_digest}</dd></div><div><dt>Status</dt><dd>{selectedSection.instance.status} / round {selectedSection.instance.current_round}</dd></div></dl> : <div className="setup-inline-form"><select aria-label="Registered pack" value={packKey} onChange={(event) => setPackKey(event.target.value)}>{state.packs.map((pack) => <option key={`${pack.pack_key}@${pack.pack_version}`} value={`${pack.pack_key}@${pack.pack_version}`}>{pack.display_name} — {pack.pack_version}</option>)}</select><button type="button" onClick={bindPack} disabled={!selectedPack}>Bind pack</button></div>}
          </section>
          <section className="setup-card" aria-labelledby="lifecycle-heading">
            <h3 id="lifecycle-heading">Lifecycle actions</h3>
            <p className="muted-copy">Clone creates a copy of this section with the same configuration. Archive marks a completed instance as read-only. Reset clears all runtime state for a setup instance.</p>
            <div className="setup-inline-form">
              {selectedSection.instance && <button type="button" onClick={() => setCloneModal({ open: true, sectionId: selectedSection.id, code: "", name: "" })}>Clone section</button>}
              {selectedSection.instance?.status === "completed" && <button type="button" onClick={() => setArchiveModal({ open: true, instanceId: selectedSection.instance.instance_id, confirmId: "" })}>Archive instance</button>}
              {selectedSection.instance?.status === "setup" && <button type="button" onClick={() => setResetModal({ open: true, instanceId: selectedSection.instance.instance_id, confirmId: "" })}>Reset instance</button>}
            </div>
          </section>
          <section className="setup-card" aria-labelledby="roster-heading">
            <div className="setup-card__heading"><h3 id="roster-heading">Roster and teams</h3><button type="button" onClick={createTeam} disabled={!selectedSection.instance}>Create team</button></div>
            <form className="setup-inline-form" onSubmit={enrollStudent}><input aria-label="Existing student user ID" inputMode="numeric" placeholder="Existing student user ID" value={studentId} onChange={(event) => setStudentId(event.target.value)} required /><button type="submit" disabled={!selectedSection.instance}>Enroll existing identity</button></form>
            {state.roster.length === 0 ? <p className="muted-copy">No enrolled identities yet.</p> : <div className="setup-table-wrap"><table className="setup-table"><thead><tr><th>Student</th><th>Email</th><th>Role</th><th>Team</th></tr></thead><tbody>{state.roster.map((row) => <tr key={row.enrollment_id}><td>{row.name}<small>{row.student_id || "No student ID"}</small></td><td>{row.email}</td><td>{row.role}</td><td><select aria-label={`Team for ${row.name}`} value={row.team?.id || ""} onChange={(event) => assign(row.enrollment_id, event.target.value)}><option value="">Unassigned</option>{state.teams.map((team) => <option key={team.id} value={team.id}>{team.name} ({team.member_count})</option>)}</select></td></tr>)}</tbody></table></div>}
          </section>
          {selectedSection.instance && <section className="setup-card" aria-labelledby="start-heading">
            <h3 id="start-heading">Start simulation</h3>
            {selectedSection.instance.status === "setup" ? <>
              <p className="muted-copy">Choose each team’s agreed starting strategy. Changing strategy later incurs the case’s switching costs and organisational disruption.</p>
              {!start.readiness ? <p>Checking section readiness…</p> : <>
                {start.readiness.blocked_reasons.length > 0 && <ul>{start.readiness.blocked_reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul>}
                {start.readiness.teams.map((team) => <label key={team.team_id}>{team.name} — starting strategy
                  <select aria-label={`Starting strategy for ${team.name}`} value={start.choices[team.team_id] || ""} onChange={(event) => setStart((previous) => ({ ...previous, choices: { ...previous.choices, [team.team_id]: event.target.value } }))}>
                    <option value="">Choose the agreed strategy</option>
                    {start.readiness.strategies.map((strategy) => <option key={strategy.key} value={strategy.key}>{strategy.label}</option>)}
                  </select>
                </label>)}
                <button type="button" className="btn-primary" disabled={!start.readiness.ready || !start.readiness.teams.every((team) => start.readiness.strategies.some((strategy) => strategy.key === start.choices[team.team_id]))} onClick={() => setStart((previous) => ({ ...previous, confirm: true }))}>Start simulation</button>
              </>}
            </> : <>
              <p>{selectedSection.instance.status} / round {selectedSection.instance.current_round}</p>
              <button type="button" onClick={() => navigate("/instructor/round-control", { state: { courseId: state.courseId, sectionId: state.sectionId } })}>Open round controls</button>
            </>}
          </section>}
        </>}
      </>}
      </fieldset>
    </div>
    {start.confirm && <div className="modal-overlay" onClick={() => { if (!start.pending) setStart((previous) => ({ ...previous, confirm: false })); }}>
      <div className="modal-dialog modal-body" role="dialog" aria-modal="true" aria-labelledby="start-confirm-heading" onClick={(event) => event.stopPropagation()}>
        <h3 id="start-confirm-heading">Start this simulation?</h3>
        <p>{selectedSection.section_name} · {selectedSection.instance.pack_key} · {start.readiness.total_rounds} rounds</p>
        <ul>{start.readiness.teams.map((team) => <li key={team.team_id}>{team.name}: {start.readiness.strategies.find((strategy) => strategy.key === start.choices[team.team_id])?.label}</li>)}</ul>
        <div className="modal-actions">
          <button type="button" disabled={start.pending} onClick={() => setStart((previous) => ({ ...previous, confirm: false }))}>Cancel</button>
          <button type="button" className="btn-primary" disabled={start.pending} onClick={handleStart}>{start.pending ? "Starting…" : "Confirm start"}</button>
        </div>
      </div>
    </div>}
    {cloneModal.open && <div className="modal-overlay" onClick={() => setCloneModal({ open: false, sectionId: null, code: "", name: "" })}>
      <div className="modal-dialog modal-body" onClick={(e) => e.stopPropagation()}>
        <h3>Clone section</h3>
        <p>Create a new section with the same pack, teams, and settings. No enrollments or runtime state will be copied.</p>
        <label>Section code (optional)<input aria-label="Clone section code" placeholder="Leave blank for default" value={cloneModal.code} onChange={(e) => setCloneModal({ ...cloneModal, code: e.target.value })} /></label>
        <label>Section name (optional)<input aria-label="Clone section name" placeholder="Leave blank for default" value={cloneModal.name} onChange={(e) => setCloneModal({ ...cloneModal, name: e.target.value })} /></label>
        <div className="modal-actions">
          <button type="button" onClick={() => setCloneModal({ open: false, sectionId: null, code: "", name: "" })}>Cancel</button>
          <button type="button" className="btn-primary" onClick={handleClone}>Clone</button>
        </div>
      </div>
    </div>}
    {archiveModal.open && <div className="modal-overlay" onClick={() => setArchiveModal({ open: false, instanceId: null, confirmId: "" })}>
      <div className="modal-dialog modal-body" onClick={(e) => e.stopPropagation()}>
        <h3>Archive instance</h3>
        <p>This will mark instance <strong>{archiveModal.instanceId}</strong> as archived (read-only). This action cannot be undone.</p>
        <label>Type the instance ID to confirm<input aria-label="Confirm instance ID" placeholder={`${archiveModal.instanceId}`} value={archiveModal.confirmId} onChange={(e) => setArchiveModal({ ...archiveModal, confirmId: e.target.value })} /></label>
        <div className="modal-actions">
          <button type="button" onClick={() => setArchiveModal({ open: false, instanceId: null, confirmId: "" })}>Cancel</button>
          <button type="button" className="btn-danger" disabled={Number(archiveModal.confirmId) !== archiveModal.instanceId} onClick={handleArchive}>Archive</button>
        </div>
      </div>
    </div>}
    {resetModal.open && <div className="modal-overlay" onClick={() => setResetModal({ open: false, instanceId: null, confirmId: "" })}>
      <div className="modal-dialog modal-body" onClick={(e) => e.stopPropagation()}>
        <h3>Reset instance</h3>
        <p>This will delete <strong>all runtime state</strong> (runs, sheets, checkpoints, results, schedules, grades) for instance <strong>{resetModal.instanceId}</strong>. Teams and settings are preserved. Export grades first if needed.</p>
        <label>Type the instance ID to confirm<input aria-label="Confirm instance ID" placeholder={`${resetModal.instanceId}`} value={resetModal.confirmId} onChange={(e) => setResetModal({ ...resetModal, confirmId: e.target.value })} /></label>
        <div className="modal-actions">
          <button type="button" onClick={() => setResetModal({ open: false, instanceId: null, confirmId: "" })}>Cancel</button>
          <button type="button" className="btn-danger" disabled={Number(resetModal.confirmId) !== resetModal.instanceId} onClick={handleReset}>Reset</button>
        </div>
      </div>
    </div>}
  </AppShell>;
}
