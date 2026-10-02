import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import AppShell from "../components/AppShell.jsx";
import {
  apiClient,
  getCurrentUser,
  listInstructorCourses,
  clearAccessToken,
} from "../api/client.js";

function requestError(error) {
  return error.response?.data?.detail || "The grading workspace could not complete that action.";
}

export default function InstructorGrading() {
  const navigate = useNavigate();
  const [state, setState] = useState({
    loading: true,
    me: null,
    courses: [],
    courseId: null,
    sections: [],
    sectionId: null,
    instanceId: null,
    grades: null,
    error: "",
    notice: "",
  });
  const [weights, setWeights] = useState({
    weight_financial: 0.25,
    weight_customer: 0.25,
    weight_internal_process: 0.25,
    weight_learning_growth: 0.25,
    rounds_mode: "final",
  });
  const [editOverride, setEditOverride] = useState(null);
  const loadSerial = useRef(0);

  const load = useCallback(async (courseId = null, sectionId = null) => {
    const serial = ++loadSerial.current;
    try {
      const [meResp, coursesResp] = await Promise.all([getCurrentUser(), listInstructorCourses()]);
      const courses = coursesResp.data;
      const selectedCourseId = courseId || courses[0]?.id || null;
      const setupResp = selectedCourseId ? await apiClient.get(`/instructor/courses/${selectedCourseId}/setup`) : { data: null };
      const setup = setupResp.data;
      const sections = setup?.sections || [];
      const selectedSectionId = sectionId || sections[0]?.id || null;
      const selectedSection = sections.find((s) => s.id === selectedSectionId);
      const instanceId = selectedSection?.instance?.instance_id || null;

      let grades = null;
      if (instanceId) {
        const gradesResp = await apiClient.get(`/instructor/instances/${instanceId}/grades`);
        grades = gradesResp.data;
      }

      if (serial !== loadSerial.current) return;

      if (grades?.config) {
        setWeights({
          weight_financial: grades.config.weight_financial,
          weight_customer: grades.config.weight_customer,
          weight_internal_process: grades.config.weight_internal_process,
          weight_learning_growth: grades.config.weight_learning_growth,
          rounds_mode: grades.config.rounds_mode,
        });
      }

      setState((prev) => ({
        ...prev,
        loading: false,
        me: meResp.data,
        courses,
        courseId: selectedCourseId,
        sections,
        sectionId: selectedSectionId,
        instanceId,
        grades,
        error: "",
      }));
    } catch (error) {
      if (serial !== loadSerial.current) return;
      if ([401, 403].includes(error.response?.status)) {
        clearAccessToken();
        navigate("/login", { replace: true });
        return;
      }
      setState((prev) => ({ ...prev, loading: false, error: requestError(error) }));
    }
  }, [navigate]);

  useEffect(() => { load(); }, [load]);

  async function saveConfig(event) {
    event.preventDefault();
    if (!state.instanceId) return;
    try {
      await apiClient.put(`/instructor/instances/${state.instanceId}/grades/config`, weights);
      setState((prev) => ({ ...prev, notice: "Grade configuration saved.", error: "" }));
      await load(state.courseId, state.sectionId);
    } catch (error) {
      setState((prev) => ({ ...prev, error: requestError(error), notice: "" }));
    }
  }

  async function saveOverride(event) {
    event.preventDefault();
    if (!state.instanceId || !editOverride) return;
    try {
      await apiClient.put(
        `/instructor/instances/${state.instanceId}/grades/teams/${editOverride.team_id}`,
        { override: editOverride.override || null, reason: editOverride.reason || null }
      );
      setEditOverride(null);
      setState((prev) => ({ ...prev, notice: "Override saved.", error: "" }));
      await load(state.courseId, state.sectionId);
    } catch (error) {
      setState((prev) => ({ ...prev, error: requestError(error), notice: "" }));
    }
  }

  function exportCSV() {
    if (!state.instanceId) return;
    const token = window.sessionStorage.getItem("mis_sim.access_token");
    const link = document.createElement("a");
    link.href = `/api/instructor/instances/${state.instanceId}/grades/export`;
    // Use fetch with auth header for proper download
    fetch(`/api/instructor/instances/${state.instanceId}/grades/export`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((resp) => resp.blob())
      .then((blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "grades.csv";
        a.click();
        URL.revokeObjectURL(url);
      })
      .catch(() => setState((prev) => ({ ...prev, error: "Export failed." })));
  }

  function selectCourse(event) {
    const courseId = Number(event.target.value);
    setState((prev) => ({ ...prev, courseId, sectionId: null, grades: null }));
    load(courseId, null);
  }

  function selectSection(event) {
    const sectionId = Number(event.target.value);
    setState((prev) => ({ ...prev, sectionId, grades: null }));
    load(state.courseId, sectionId);
  }

  function fmt(value) {
    if (value === null || value === undefined) return "\u2014";
    return typeof value === "number" ? value.toFixed(4) : String(value);
  }

  const weightsSum = weights.weight_financial + weights.weight_customer + weights.weight_internal_process + weights.weight_learning_growth;
  const weightsValid = Math.abs(weightsSum - 1.0) <= 0.01;

  if (state.loading) return <main className="app-shell plain-state"><p>Loading grading workspace...</p></main>;

  return (
    <AppShell me={state.me} activePath="/instructor/grading" pageTitle="Grading and export">
      <div className="instructor-workspace">
        <header className="page-header">
          <p className="eyebrow">M5.5</p>
          <h2>Grade derivation and CSV export</h2>
          <p className="page-intro">View derived grades from completed rounds, configure BSC weights, set instructor overrides, and export grades as CSV.</p>
        </header>

        {state.error && <p className="workspace-message workspace-message--error" role="alert">{state.error}</p>}
        {state.notice && <p className="workspace-message workspace-message--ok" role="status">{state.notice}</p>}

        <section className="setup-card" aria-labelledby="grading-course-heading">
          <h3 id="grading-course-heading">Course and section</h3>
          <label>Course
            <select value={state.courseId || ""} onChange={selectCourse}>
              <option value="">Select course</option>
              {state.courses.map((c) => <option key={c.id} value={c.id}>{c.course_code} - {c.course_name}</option>)}
            </select>
          </label>
          {state.sections.length > 0 && (
            <label>Section
              <select value={state.sectionId || ""} onChange={selectSection}>
                {state.sections.map((s) => <option key={s.id} value={s.id}>{s.section_code} - {s.section_name}</option>)}
              </select>
            </label>
          )}
        </section>

        {state.instanceId && (
          <>
            <section className="setup-card" aria-labelledby="weights-heading">
              <h3 id="weights-heading">Grade configuration</h3>
              <form onSubmit={saveConfig} className="setup-inline-form" style={{ flexWrap: "wrap", gap: "0.5rem" }}>
                <label>Financial<input type="number" step="0.01" min="0" max="1" value={weights.weight_financial} onChange={(e) => setWeights({ ...weights, weight_financial: parseFloat(e.target.value) || 0 })} style={{ width: "5rem" }} /></label>
                <label>Customer<input type="number" step="0.01" min="0" max="1" value={weights.weight_customer} onChange={(e) => setWeights({ ...weights, weight_customer: parseFloat(e.target.value) || 0 })} style={{ width: "5rem" }} /></label>
                <label>Internal process<input type="number" step="0.01" min="0" max="1" value={weights.weight_internal_process} onChange={(e) => setWeights({ ...weights, weight_internal_process: parseFloat(e.target.value) || 0 })} style={{ width: "5rem" }} /></label>
                <label>Learning/growth<input type="number" step="0.01" min="0" max="1" value={weights.weight_learning_growth} onChange={(e) => setWeights({ ...weights, weight_learning_growth: parseFloat(e.target.value) || 0 })} style={{ width: "5rem" }} /></label>
                <label>Mode
                  <select value={weights.rounds_mode} onChange={(e) => setWeights({ ...weights, rounds_mode: e.target.value })}>
                    <option value="final">Final round</option>
                    <option value="average">Average all rounds</option>
                  </select>
                </label>
                {!weightsValid && <span style={{ color: "var(--color-danger, red)" }}>Weights must sum to 1.0 (current: {weightsSum.toFixed(4)})</span>}
                <button type="submit" disabled={!weightsValid}>Save weights</button>
              </form>
            </section>

            <section className="setup-card" aria-labelledby="grades-heading">
              <div className="setup-card__heading">
                <h3 id="grades-heading">Team grades</h3>
                <button type="button" onClick={exportCSV}>Export CSV</button>
              </div>
              {state.grades?.teams?.length ? (
                <div className="setup-table-wrap">
                  <table className="setup-table">
                    <thead>
                      <tr>
                        <th>Team</th>
                        <th>Strategy</th>
                        <th>Realised value</th>
                        <th>Financial</th>
                        <th>Customer</th>
                        <th>Internal process</th>
                        <th>Learning/growth</th>
                        <th>Derived grade</th>
                        <th>Override</th>
                        <th>Final grade</th>
                        <th>Reason</th>
                        <th></th>
                      </tr>
                    </thead>
                    <tbody>
                      {state.grades.teams.map((team) => (
                        <tr key={team.team_id}>
                          <td>{team.team_name}</td>
                          <td>{team.strategy || "\u2014"}</td>
                          <td>{fmt(team.final_realised_value)}</td>
                          <td>{fmt(team.scorecard?.financial)}</td>
                          <td>{fmt(team.scorecard?.customer)}</td>
                          <td>{fmt(team.scorecard?.internal_process)}</td>
                          <td>{fmt(team.scorecard?.learning_growth)}</td>
                          <td>{fmt(team.derived_grade)}</td>
                          <td>{fmt(team.override)}</td>
                          <td><strong>{fmt(team.final_grade)}</strong></td>
                          <td>{team.override_reason || ""}</td>
                          <td><button type="button" onClick={() => setEditOverride({ team_id: team.team_id, team_name: team.team_name, override: team.override, reason: team.override_reason || "" })}>Edit</button></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="muted-copy">No teams or no grade data available.</p>
              )}
            </section>
          </>
        )}

        {editOverride && (
          <div className="modal-backdrop" onClick={() => setEditOverride(null)} style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.3)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}>
            <form onSubmit={saveOverride} onClick={(e) => e.stopPropagation()} style={{ background: "var(--color-surface, #fff)", padding: "1.5rem", borderRadius: "0.5rem", minWidth: "20rem" }}>
              <h3>Override for {editOverride.team_name}</h3>
              <label>Override grade<input type="number" step="0.01" min="0" max="1" value={editOverride.override ?? ""} onChange={(e) => setEditOverride({ ...editOverride, override: e.target.value === "" ? null : parseFloat(e.target.value) })} style={{ width: "100%" }} /></label>
              <label>Reason<input type="text" maxLength={256} value={editOverride.reason} onChange={(e) => setEditOverride({ ...editOverride, reason: e.target.value })} style={{ width: "100%" }} /></label>
              <div style={{ display: "flex", gap: "0.5rem", marginTop: "1rem" }}>
                <button type="submit">Save</button>
                <button type="button" onClick={() => setEditOverride(null)}>Cancel</button>
              </div>
            </form>
          </div>
        )}
      </div>
    </AppShell>
  );
}
