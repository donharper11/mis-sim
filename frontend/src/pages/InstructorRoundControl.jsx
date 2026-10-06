import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import AppShell from "../components/AppShell.jsx";
import StatusBadge from "../components/StatusBadge.jsx";
import {
  apiClient,
  getCurrentUser,
  listInstructorCourses,
  getCourseSetup,
  clearAccessToken,
} from "../api/client.js";

function requestError(error) {
  const detail = error.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (detail?.code) return `${detail.code}: ${detail.field || ""}`;
  return "The round control workspace could not complete that action.";
}

function roundStatusBadge(status) {
  const states = { draft: "info", locked: "needs-attention", completed: "complete", active: "info", paused: "needs-attention", setup: "neutral" };
  return <StatusBadge status={states[status] || "neutral"} label={status} />;
}

export default function InstructorRoundControl() {
  const navigate = useNavigate();
  const [state, setState] = useState({
    loading: true, me: null, courses: [], setup: null, courseId: null,
    sectionId: null, instance: null, teams: [], schedule: null, settings: {},
    error: "", notice: "",
  });
  const loadSerial = useRef(0);

  const load = useCallback(async (courseId = null, sectionId = null) => {
    const serial = ++loadSerial.current;
    try {
      const [meResp, coursesResp] = await Promise.all([getCurrentUser(), listInstructorCourses()]);
      const courses = coursesResp.data;
      const selectedCourseId = courseId || courses[0]?.id || null;
      const setupResp = selectedCourseId ? await getCourseSetup(selectedCourseId) : { data: null };
      const setup = setupResp.data;
      const selectedSectionId = sectionId || setup?.sections?.[0]?.id || null;
      const selectedSection = setup?.sections?.find((s) => s.id === selectedSectionId);
      const instance = selectedSection?.instance || null;

      let schedule = null;
      let settings = {};
      let teams = [];
      if (instance) {
        try {
          const schedResp = await apiClient.get(`/instances/${instance.instance_id}/round-control/schedule`);
          schedule = schedResp.data;
        } catch { /* schedule may not exist yet */ }
        try {
          const instResp = await apiClient.get(`/instances/${instance.instance_id}`);
          settings = instResp.data?.settings || {};
        } catch { /* ignore */ }
        try {
          const teamsResp = await apiClient.get(`/instances/${instance.instance_id}/teams`);
          teams = teamsResp.data || [];
        } catch { /* ignore */ }
      }

      if (serial !== loadSerial.current) return;
      setState((prev) => ({
        ...prev, loading: false, me: meResp.data, courses, setup,
        courseId: selectedCourseId, sectionId: selectedSectionId, instance,
        schedule, settings, teams, error: "",
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

  async function perform(action, success) {
    try {
      await action();
      setState((prev) => ({ ...prev, notice: success, error: "" }));
      await load(state.courseId, state.sectionId);
    } catch (error) {
      setState((prev) => ({ ...prev, error: requestError(error), notice: "" }));
    }
  }

  async function pauseInstance() {
    if (!state.instance) return;
    await perform(() => apiClient.post(`/instances/${state.instance.instance_id}/round-control/pause`), "Instance paused.");
  }

  async function resumeInstance() {
    if (!state.instance) return;
    await perform(() => apiClient.post(`/instances/${state.instance.instance_id}/round-control/resume`), "Instance resumed.");
  }

  async function lockAll() {
    if (!state.instance) return;
    await perform(() => apiClient.post(`/instances/${state.instance.instance_id}/round-control/lock`), "All teams locked.");
  }

  async function advanceAll() {
    if (!state.instance) return;
    await perform(() => apiClient.post(`/instances/${state.instance.instance_id}/round-control/advance`), "Round advanced.");
  }

  async function reopenTeam(teamId) {
    if (!state.instance) return;
    await perform(() => apiClient.post(`/instances/${state.instance.instance_id}/round-control/reopen`, { team_id: teamId }), `Team ${teamId} reopened.`);
  }

  async function saveSettings(updates) {
    if (!state.instance) return;
    await perform(() => apiClient.patch(`/instances/${state.instance.instance_id}/settings`, updates), "Settings saved.");
  }

  function selectCourse(event) {
    const id = Number(event.target.value);
    setState((prev) => ({ ...prev, courseId: id, sectionId: null, setup: null, instance: null, teams: [], schedule: null, settings: {}, error: "" }));
    load(id, null);
  }

  function selectSection(event) {
    const id = Number(event.target.value);
    setState((prev) => ({ ...prev, sectionId: id, instance: null, teams: [], schedule: null, settings: {}, error: "" }));
    load(state.courseId, id);
  }

  if (state.loading) return <main className="app-shell plain-state"><p>Loading round control...</p></main>;

  const instance = state.instance;
  const isPaused = instance?.status === "paused";
  const isActive = instance?.status === "active";
  const scheduleRounds = state.schedule?.rounds || [];

  return (
    <AppShell me={state.me} activePath="/instructor/round-control" pageTitle="Round control">
      <div className="instructor-workspace">
        <header className="page-header">
          <p className="eyebrow">M5.3</p>
          <h2>Round control</h2>
          <p className="page-intro">Manage round progression, lock and reopen teams, pause the instance, and configure schedule settings.</p>
        </header>

        {state.error && <p className="workspace-message workspace-message--error" role="alert">{state.error}</p>}
        {state.notice && <p className="workspace-message workspace-message--ok" role="status">{state.notice}</p>}

        {/* Course / section selector */}
        <section className="setup-card" aria-labelledby="rc-course-heading">
          <h3 id="rc-course-heading">Select instance</h3>
          <label>
            Course
            <select value={state.courseId || ""} onChange={selectCourse}>
              <option value="">Choose a course</option>
              {state.courses.map((c) => <option key={c.id} value={c.id}>{c.course_code} -- {c.course_name}</option>)}
            </select>
          </label>
          {state.setup && (
            <label>
              Section
              <select value={state.sectionId || ""} onChange={selectSection}>
                {state.setup.sections.map((s) => <option key={s.id} value={s.id}>{s.section_code} -- {s.section_name}</option>)}
              </select>
            </label>
          )}
        </section>

        {instance && (
          <>
            {/* Instance status and controls */}
            <section className="setup-card" aria-labelledby="rc-status-heading">
              <h3 id="rc-status-heading">Instance status</h3>
              <dl className="setup-facts">
                <div><dt>Status</dt><dd>{roundStatusBadge(instance.status)}</dd></div>
                <div><dt>Round</dt><dd>{Math.max(instance.current_round, 1)} of {instance.total_rounds}</dd></div>
                <div><dt>Pack</dt><dd>{instance.pack_key} {instance.pack_version}</dd></div>
              </dl>
              <div className="setup-inline-form">
                {isActive && <button type="button" onClick={pauseInstance}>Pause instance</button>}
                {isPaused && <button type="button" onClick={resumeInstance}>Resume instance</button>}
                <button type="button" onClick={lockAll} disabled={isPaused || instance.status === "completed"}>Lock all</button>
                <button type="button" onClick={advanceAll} disabled={isPaused || instance.status === "completed"}>Advance round</button>
              </div>
            </section>

            {/* Team round grid */}
            <section className="setup-card" aria-labelledby="rc-teams-heading">
              <h3 id="rc-teams-heading">Team status</h3>
              {state.teams.length === 0
                ? <p className="muted-copy">No teams configured for this instance.</p>
                : (
                  <div className="setup-table-wrap">
                    <table className="setup-table">
                      <thead>
                        <tr><th>Team</th><th>Status</th><th>Actions</th></tr>
                      </thead>
                      <tbody>
                        {state.teams.map((team) => {
                          // Try to find team status from schedule data
                          const currentScheduleRound = scheduleRounds.find((r) => r.round_number === Math.max(instance.current_round, 1));
                          const teamSchedule = currentScheduleRound?.teams?.find((t) => t.team_id === team.id);
                          const teamLocked = teamSchedule?.locked_at != null;
                          const teamAdvanced = teamSchedule?.advanced_at != null;
                          return (
                            <tr key={team.id}>
                              <td>{team.name}<small>ID: {team.id}</small></td>
                              <td>
                                {teamAdvanced ? roundStatusBadge("completed") : teamLocked ? roundStatusBadge("locked") : roundStatusBadge("draft")}
                              </td>
                              <td>
                                {teamLocked && !teamAdvanced && (
                                  <button type="button" onClick={() => reopenTeam(team.id)} style={{ fontSize: 12 }}>Reopen</button>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )
              }
            </section>

            {/* Schedule display */}
            {scheduleRounds.length > 0 && (
              <section className="setup-card" aria-labelledby="rc-schedule-heading">
                <h3 id="rc-schedule-heading">Schedule</h3>
                <div className="setup-table-wrap">
                  <table className="setup-table">
                    <thead>
                      <tr><th>Round</th><th>Start</th><th>Deadline</th><th>Auto-advance</th><th>Grace (min)</th><th>Locked</th></tr>
                    </thead>
                    <tbody>
                      {scheduleRounds.map((round) => (
                        <tr key={round.round_number}>
                          <td>{round.round_number}</td>
                          <td>{new Date(round.start_at).toLocaleString()}</td>
                          <td>{new Date(round.deadline).toLocaleString()}</td>
                          <td>{round.auto_advance ? "Yes" : "No"}</td>
                          <td>{round.grace_period_minutes}</td>
                          <td>{round.decisions_locked ? roundStatusBadge("locked") : roundStatusBadge("draft")}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            )}

            {/* Settings editor */}
            <section className="setup-card" aria-labelledby="rc-settings-heading">
              <h3 id="rc-settings-heading">Schedule settings</h3>
              <SettingsEditor settings={state.settings} onSave={saveSettings} />
            </section>
          </>
        )}
      </div>
    </AppShell>
  );
}

/* eslint-disable react/prop-types */
function SettingsEditor({ settings, onSave }) {
  const [form, setForm] = useState({
    default_round_duration_hours: settings.default_round_duration_hours ?? 24,
    auto_advance_on_deadline: settings.auto_advance_on_deadline ?? false,
    grace_period_minutes: settings.grace_period_minutes ?? 30,
    lock_warning_minutes: settings.lock_warning_minutes ?? 15,
  });

  useEffect(() => {
    setForm({
      default_round_duration_hours: settings.default_round_duration_hours ?? 24,
      auto_advance_on_deadline: settings.auto_advance_on_deadline ?? false,
      grace_period_minutes: settings.grace_period_minutes ?? 30,
      lock_warning_minutes: settings.lock_warning_minutes ?? 15,
    });
  }, [settings]);

  function handleSubmit(event) {
    event.preventDefault();
    onSave({
      default_round_duration_hours: Number(form.default_round_duration_hours),
      auto_advance_on_deadline: form.auto_advance_on_deadline,
      grace_period_minutes: Number(form.grace_period_minutes),
      lock_warning_minutes: Number(form.lock_warning_minutes),
    });
  }

  return (
    <form className="setup-inline-form" onSubmit={handleSubmit} style={{ flexDirection: "column", alignItems: "flex-start", gap: 12 }}>
      <label>
        Round duration (hours)
        <input type="number" min="0.5" step="0.5" value={form.default_round_duration_hours} onChange={(e) => setForm({ ...form, default_round_duration_hours: e.target.value })} />
      </label>
      <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <input type="checkbox" checked={form.auto_advance_on_deadline} onChange={(e) => setForm({ ...form, auto_advance_on_deadline: e.target.checked })} />
        Auto-advance on deadline
      </label>
      <label>
        Grace period (minutes)
        <input type="number" min="0" value={form.grace_period_minutes} onChange={(e) => setForm({ ...form, grace_period_minutes: e.target.value })} />
      </label>
      <label>
        Lock warning (minutes)
        <input type="number" min="0" value={form.lock_warning_minutes} onChange={(e) => setForm({ ...form, lock_warning_minutes: e.target.value })} />
      </label>
      <button type="submit">Save settings</button>
    </form>
  );
}
