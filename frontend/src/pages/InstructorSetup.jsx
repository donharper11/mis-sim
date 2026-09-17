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
  return error.response?.data?.detail || "The instructor workspace could not complete that action.";
}

export default function InstructorSetup() {
  const navigate = useNavigate();
  const [state, setState] = useState({ loading: true, me: null, courses: [], packs: [], setup: null, courseId: null, sectionId: null, roster: [], teams: [], error: "", notice: "" });
  const [newCourse, setNewCourse] = useState({ course_code: "", course_name: "", academic_year: "2026", semester: "A" });
  const [newSection, setNewSection] = useState({ section_code: "", section_name: "" });
  const [packKey, setPackKey] = useState("");
  const [studentId, setStudentId] = useState("");
  const loadSerial = useRef(0);

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
      if (serial !== loadSerial.current) return;
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
          <section className="setup-card" aria-labelledby="roster-heading">
            <div className="setup-card__heading"><h3 id="roster-heading">Roster and teams</h3><button type="button" onClick={createTeam} disabled={!selectedSection.instance}>Create team</button></div>
            <form className="setup-inline-form" onSubmit={enrollStudent}><input aria-label="Existing student user ID" inputMode="numeric" placeholder="Existing student user ID" value={studentId} onChange={(event) => setStudentId(event.target.value)} required /><button type="submit" disabled={!selectedSection.instance}>Enroll existing identity</button></form>
            {state.roster.length === 0 ? <p className="muted-copy">No enrolled identities yet.</p> : <div className="setup-table-wrap"><table className="setup-table"><thead><tr><th>Student</th><th>Email</th><th>Role</th><th>Team</th></tr></thead><tbody>{state.roster.map((row) => <tr key={row.enrollment_id}><td>{row.name}<small>{row.student_id || "No student ID"}</small></td><td>{row.email}</td><td>{row.role}</td><td><select aria-label={`Team for ${row.name}`} value={row.team?.id || ""} onChange={(event) => assign(row.enrollment_id, event.target.value)}><option value="">Unassigned</option>{state.teams.map((team) => <option key={team.id} value={team.id}>{team.name} ({team.member_count})</option>)}</select></td></tr>)}</tbody></table></div>}
          </section>
        </>}
      </>}
    </div>
  </AppShell>;
}
