import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiClient, clearAccessToken } from "../api/client.js";
import AppShell from "../components/AppShell.jsx";
import Dashboard from "./Dashboard.jsx";

export default function Shell() {
  const navigate = useNavigate();
  const [state, setState] = useState({ status: "loading", me: null, instance: null, schedule: null, dashboard: null, error: "" });

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const meResponse = await apiClient.get("/auth/me");
        const me = meResponse.data;
        let instance = null;
        let schedule = null;
        let dashboard = null;
        if (me.instance_id) {
          const instanceResponse = await apiClient.get(`/instances/${me.instance_id}`);
          instance = instanceResponse.data;
          const scheduleResponse = await apiClient.get(`/instances/${me.instance_id}/schedule`);
          schedule = scheduleResponse.data;
          const dashboardResponse = await apiClient.get(`/instances/${me.instance_id}/dashboard`);
          dashboard = dashboardResponse.data;
        }
        if (active) setState({ status: "ready", me, instance, schedule, dashboard, error: "" });
      } catch (requestError) {
        if (!active) return;
        if (requestError.response?.status === 401 || requestError.response?.status === 403) {
          clearAccessToken();
          navigate("/login", { replace: true });
          return;
        }
        setState({ status: "error", me: null, instance: null, schedule: null, dashboard: null, error: requestError.response?.data?.detail || "The simulation context could not be loaded." });
      }
    }
    load();
    return () => { active = false; };
  }, [navigate]);

  if (state.status === "loading") return <main className="app-shell plain-state"><p>Loading your simulation…</p></main>;
  if (state.status === "error") return <main className="app-shell plain-state"><h1>We could not open this simulation</h1><p role="alert">{state.error}</p></main>;
  return <AppShell me={state.me} instance={state.instance} schedule={state.schedule} dashboard={state.dashboard}><Dashboard data={state.dashboard} /></AppShell>;
}
