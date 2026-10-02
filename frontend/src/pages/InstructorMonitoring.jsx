/* eslint-disable react/prop-types */
import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import AppShell from "../components/AppShell.jsx";
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
  return "The monitoring dashboard could not load data.";
}

function StatusBadge({ status }) {
  const colors = { draft: "#1890ff", locked: "#faad14", completed: "#52c41a", active: "#1890ff", paused: "#ff4d4f", setup: "#d9d9d9", uninitialized: "#bfbfbf" };
  return (
    <span style={{ display: "inline-block", padding: "2px 8px", borderRadius: 4, fontSize: 12, fontWeight: 600, background: colors[status] || "#d9d9d9", color: "#fff" }}>
      {status}
    </span>
  );
}

function ScorecardBar({ value, label }) {
  if (value == null) return <span className="muted-copy">--</span>;
  const pct = Math.round(value * 100);
  const color = pct >= 70 ? "#52c41a" : pct >= 50 ? "#faad14" : "#ff4d4f";
  return (
    <span title={`${label}: ${pct}%`} style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
      <span style={{ display: "inline-block", width: 48, height: 8, background: "#f0f0f0", borderRadius: 4, overflow: "hidden" }}>
        <span style={{ display: "block", width: `${pct}%`, height: "100%", background: color, borderRadius: 4 }} />
      </span>
      <span style={{ fontSize: 11, color: "#595959", minWidth: 28 }}>{pct}%</span>
    </span>
  );
}

function ScorecardSparkline({ rounds }) {
  if (!rounds || rounds.length === 0) return <span className="muted-copy">No data</span>;
  const dimensions = ["financial", "customer", "internal_process", "learning_growth"];
  const colors = { financial: "#1890ff", customer: "#52c41a", internal_process: "#faad14", learning_growth: "#722ed1" };
  return (
    <div style={{ display: "flex", gap: 2, alignItems: "flex-end", height: 32 }}>
      {rounds.map((r) => (
        <div key={r.round} style={{ display: "flex", flexDirection: "column", gap: 1, alignItems: "center" }}>
          {dimensions.map((dim) => {
            const val = r.scorecard?.[dim];
            const h = val != null ? Math.max(2, Math.round(val * 24)) : 2;
            return (
              <span
                key={dim}
                title={`R${r.round} ${dim}: ${val != null ? Math.round(val * 100) + "%" : "--"}`}
                style={{ display: "block", width: 6, height: h, background: val != null ? colors[dim] : "#f0f0f0", borderRadius: 1 }}
              />
            );
          })}
          <span style={{ fontSize: 8, color: "#8c8c8c" }}>{r.round}</span>
        </div>
      ))}
    </div>
  );
}

function formatMoney(value) {
  return typeof value === "number" && Number.isFinite(value) ? `$${value.toLocaleString()}` : "--";
}

export default function InstructorMonitoring() {
  const navigate = useNavigate();
  const [state, setState] = useState({
    loading: true, me: null, courses: [], setup: null, courseId: null,
    sectionId: null, instance: null, monitoring: null, progression: null,
    error: "",
  });
  const [sortField, setSortField] = useState("team_name");
  const [sortDir, setSortDir] = useState("asc");
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

      let monitoring = null;
      let progression = null;
      if (instance) {
        try {
          const monResp = await apiClient.get(`/instructor/instances/${instance.instance_id}/monitoring`);
          monitoring = monResp.data;
        } catch { /* monitoring may not be available */ }
        if (monitoring && monitoring.teams.length > 0) {
          try {
            const teamIds = monitoring.teams.map((t) => t.team_id).join(",");
            const progResp = await apiClient.get(`/instructor/instances/${instance.instance_id}/monitoring/progression`, { params: { team_ids: teamIds } });
            progression = progResp.data;
          } catch { /* progression optional */ }
        }
      }

      if (serial !== loadSerial.current) return;
      setState((prev) => ({
        ...prev, loading: false, me: meResp.data, courses, setup,
        courseId: selectedCourseId, sectionId: selectedSectionId,
        instance, monitoring, progression, error: "",
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

  function selectCourse(event) {
    const id = Number(event.target.value);
    setState((prev) => ({ ...prev, courseId: id, sectionId: null, setup: null, instance: null, monitoring: null, progression: null, error: "" }));
    load(id, null);
  }

  function selectSection(event) {
    const id = Number(event.target.value);
    setState((prev) => ({ ...prev, sectionId: id, instance: null, monitoring: null, progression: null, error: "" }));
    load(state.courseId, id);
  }

  function toggleSort(field) {
    if (sortField === field) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDir("asc");
    }
  }

  function sortedTeams() {
    if (!state.monitoring) return [];
    const teams = [...state.monitoring.teams];
    teams.sort((a, b) => {
      let av, bv;
      if (sortField === "team_name") { av = a.team_name; bv = b.team_name; }
      else if (sortField === "current_round") { av = a.current_round; bv = b.current_round; }
      else if (sortField === "status") { av = a.status; bv = b.status; }
      else if (sortField === "open_signals_count") { av = a.open_signals_count; bv = b.open_signals_count; }
      else if (sortField === "capital_remaining") { av = a.capital_remaining ?? -Infinity; bv = b.capital_remaining ?? -Infinity; }
      else if (["financial", "customer", "internal_process", "learning_growth"].includes(sortField)) {
        av = a.scorecard?.[sortField] ?? -Infinity;
        bv = b.scorecard?.[sortField] ?? -Infinity;
      } else { av = 0; bv = 0; }
      if (typeof av === "string") return sortDir === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
      return sortDir === "asc" ? (av - bv) : (bv - av);
    });
    return teams;
  }

  function getTeamProgression(teamId) {
    if (!state.progression) return [];
    const team = state.progression.teams?.find((t) => t.team_id === teamId);
    return team?.rounds || [];
  }

  const sortArrow = (field) => sortField === field ? (sortDir === "asc" ? " ^" : " v") : "";

  if (state.loading) return <main className="app-shell plain-state"><p>Loading monitoring dashboard...</p></main>;

  const mon = state.monitoring;
  const summary = mon?.summary;

  return (
    <AppShell me={state.me} activePath="/instructor/monitoring" pageTitle="Monitoring">
      <div className="instructor-workspace">
        <header className="page-header">
          <p className="eyebrow">M5.4</p>
          <h2>Monitoring dashboard</h2>
          <p className="page-intro">Cross-team monitoring with aggregate scorecard, round progression, and attention alerts.</p>
        </header>

        {state.error && <p className="workspace-message workspace-message--error" role="alert">{state.error}</p>}

        {/* Course / section selector */}
        <section className="setup-card" aria-labelledby="mon-course-heading">
          <h3 id="mon-course-heading">Select instance</h3>
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

        {mon && (
          <>
            {/* Summary cards */}
            <section className="setup-card" aria-labelledby="mon-summary-heading">
              <h3 id="mon-summary-heading">Instance summary</h3>
              <dl className="setup-facts">
                <div><dt>Status</dt><dd><StatusBadge status={mon.instance_status} /></dd></div>
                <div><dt>Round</dt><dd>{mon.current_round} of {mon.total_rounds}</dd></div>
                <div><dt>Total teams</dt><dd>{mon.teams.length}</dd></div>
                <div><dt>Open signals</dt><dd>{summary.total_open_signals}</dd></div>
              </dl>
              <div style={{ display: "flex", gap: 24, flexWrap: "wrap", marginTop: 12 }}>
                <div>
                  <strong style={{ fontSize: 12, color: "#8c8c8c" }}>Teams by status</strong>
                  <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
                    {Object.entries(summary.teams_by_status).map(([status, count]) => (
                      <span key={status}><StatusBadge status={status} /> {count}</span>
                    ))}
                  </div>
                </div>
                <div>
                  <strong style={{ fontSize: 12, color: "#8c8c8c" }}>Average scorecard</strong>
                  <div style={{ display: "flex", flexDirection: "column", gap: 2, marginTop: 4 }}>
                    <ScorecardBar value={summary.average_scorecard.financial} label="Financial" />
                    <ScorecardBar value={summary.average_scorecard.customer} label="Customer" />
                    <ScorecardBar value={summary.average_scorecard.internal_process} label="Internal process" />
                    <ScorecardBar value={summary.average_scorecard.learning_growth} label="Learning &amp; growth" />
                  </div>
                </div>
                {summary.capital_distribution.min != null && (
                  <div>
                    <strong style={{ fontSize: 12, color: "#8c8c8c" }}>Capital distribution</strong>
                    <div style={{ marginTop: 4, fontSize: 13 }}>
                      <div>Min: {formatMoney(summary.capital_distribution.min)}</div>
                      <div>Max: {formatMoney(summary.capital_distribution.max)}</div>
                      <div>Mean: {formatMoney(summary.capital_distribution.mean)}</div>
                    </div>
                  </div>
                )}
              </div>
            </section>

            {/* Attention alerts */}
            {mon.attention.length > 0 && (
              <section className="setup-card" aria-labelledby="mon-attention-heading">
                <h3 id="mon-attention-heading">Attention</h3>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                  {mon.attention.map((alert, i) => {
                    const colors = { zero_capital: "#ff4d4f", behind_round: "#faad14", critical_signals: "#ff7a45" };
                    const labels = { zero_capital: "Zero capital", behind_round: "Behind round", critical_signals: "Critical signals" };
                    return (
                      <span key={i} style={{ display: "inline-block", padding: "4px 10px", borderRadius: 4, fontSize: 12, fontWeight: 600, background: colors[alert.reason] || "#d9d9d9", color: "#fff" }}>
                        {alert.team_name}: {labels[alert.reason] || alert.reason}
                      </span>
                    );
                  })}
                </div>
              </section>
            )}

            {/* Team table */}
            <section className="setup-card" aria-labelledby="mon-teams-heading">
              <h3 id="mon-teams-heading">Team detail</h3>
              {mon.teams.length === 0
                ? <p className="muted-copy">No teams configured for this instance.</p>
                : (
                  <div className="setup-table-wrap">
                    <table className="setup-table">
                      <thead>
                        <tr>
                          <th style={{ cursor: "pointer" }} onClick={() => toggleSort("team_name")}>Team{sortArrow("team_name")}</th>
                          <th style={{ cursor: "pointer" }} onClick={() => toggleSort("current_round")}>Round{sortArrow("current_round")}</th>
                          <th style={{ cursor: "pointer" }} onClick={() => toggleSort("status")}>Status{sortArrow("status")}</th>
                          <th style={{ cursor: "pointer" }} onClick={() => toggleSort("financial")}>Financial{sortArrow("financial")}</th>
                          <th style={{ cursor: "pointer" }} onClick={() => toggleSort("customer")}>Customer{sortArrow("customer")}</th>
                          <th style={{ cursor: "pointer" }} onClick={() => toggleSort("internal_process")}>Internal proc.{sortArrow("internal_process")}</th>
                          <th style={{ cursor: "pointer" }} onClick={() => toggleSort("learning_growth")}>Learning{sortArrow("learning_growth")}</th>
                          <th style={{ cursor: "pointer" }} onClick={() => toggleSort("open_signals_count")}>Signals{sortArrow("open_signals_count")}</th>
                          <th style={{ cursor: "pointer" }} onClick={() => toggleSort("capital_remaining")}>Capital{sortArrow("capital_remaining")}</th>
                          <th>Progression</th>
                        </tr>
                      </thead>
                      <tbody>
                        {sortedTeams().map((team) => (
                          <tr key={team.team_id}>
                            <td>{team.team_name}<small>ID: {team.team_id}</small></td>
                            <td>{team.current_round}</td>
                            <td><StatusBadge status={team.status} /></td>
                            <td><ScorecardBar value={team.scorecard?.financial} label="Financial" /></td>
                            <td><ScorecardBar value={team.scorecard?.customer} label="Customer" /></td>
                            <td><ScorecardBar value={team.scorecard?.internal_process} label="Internal process" /></td>
                            <td><ScorecardBar value={team.scorecard?.learning_growth} label="Learning &amp; growth" /></td>
                            <td>{team.open_signals_count}</td>
                            <td>{formatMoney(team.capital_remaining)}</td>
                            <td><ScorecardSparkline rounds={getTeamProgression(team.team_id)} /></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
            </section>
          </>
        )}

        {!mon && state.instance && <p className="muted-copy">No monitoring data available for this instance.</p>}
        {!state.instance && <p className="muted-copy">Select a course and section with an active instance to view monitoring data.</p>}
      </div>
    </AppShell>
  );
}
