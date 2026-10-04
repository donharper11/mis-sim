/* eslint-disable react/prop-types */
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiClient, clearAccessToken } from "../api/client.js";
import AppShell from "../components/AppShell.jsx";
import Dashboard from "./Dashboard.jsx";
import Rollout from "./Rollout.jsx";
import Review from "./Review.jsx";
import Debrief from "./Debrief.jsx";
import Controls from "./Controls.jsx";
import StrategyPage from "./StrategyPage.jsx";
import InfrastructurePage from "./InfrastructurePage.jsx";
import ApplicationsPage from "./ApplicationsPage.jsx";
import ApplicationDetailPage from "./ApplicationDetailPage.jsx";

const viewTitles = {
  dashboard: "Dashboard",
  strategy: "Strategy",
  infrastructure: "IT Infrastructure",
  applications: "Applications",
  "application-detail": "Application Detail",
  rollout: "Rollout & Adoption",
  review: "Review & Budget",
  debrief: "Debrief",
  challenges: "Challenges",
};

export default function Shell({ view = "dashboard" }) {
  const navigate = useNavigate();
  const [state, setState] = useState({ status: "loading", me: null, instance: null, schedule: null, dashboard: null, platform: null, components: null, rollout: null, review: null, debrief: null, controls: null, hostPlatforms: null, error: "" });

  useEffect(() => {
    let active = true;
    setState((prev) => ({ ...prev, status: "loading" }));
    async function load() {
      try {
        const meResponse = await apiClient.get("/auth/me");
        const me = meResponse.data;
        let instance = null;
        let schedule = null;
        let dashboard = null;
        let platform = null;
        let components = null;
        let rollout = null;
        let review = null;
        let debrief = null;
        let controls = null;
        let hostPlatforms = null;
        if (me.instance_id) {
          const instanceResponse = await apiClient.get(`/instances/${me.instance_id}`);
          instance = instanceResponse.data;
          const scheduleResponse = await apiClient.get(`/instances/${me.instance_id}/schedule`);
          schedule = scheduleResponse.data;
          const dashboardResponse = await apiClient.get(`/instances/${me.instance_id}/dashboard`);
          dashboard = dashboardResponse.data;

          // Graceful host-platforms fetch (new endpoint may not be deployed yet)
          const fetchHostPlatforms = () => apiClient.get(`/instances/${me.instance_id}/host-platforms`).then((r) => r.data.platforms).catch(() => []);

          // Parallel data fetching for merged pages
          if (view === "infrastructure") {
            const [platformResponse, controlsResponse, hp] = await Promise.all([
              apiClient.get(`/instances/${me.instance_id}/platform`),
              apiClient.get(`/instances/${me.instance_id}/controls`),
              fetchHostPlatforms(),
            ]);
            platform = platformResponse.data;
            controls = controlsResponse.data;
            hostPlatforms = hp;
          }
          if (view === "applications" || view === "application-detail") {
            const [componentsResponse, hp] = await Promise.all([
              apiClient.get(`/instances/${me.instance_id}/components`),
              fetchHostPlatforms(),
            ]);
            components = componentsResponse.data;
            hostPlatforms = hp;
          }
          if (view === "rollout") {
            const [rolloutResponse, controlsResponse] = await Promise.all([
              apiClient.get(`/instances/${me.instance_id}/rollout`),
              apiClient.get(`/instances/${me.instance_id}/controls`),
            ]);
            rollout = rolloutResponse.data;
            controls = controlsResponse.data;
          }
          if (view === "review") {
            const [reviewResponse, controlsResponse] = await Promise.all([
              apiClient.get(`/instances/${me.instance_id}/review`),
              apiClient.get(`/instances/${me.instance_id}/controls`),
            ]);
            review = reviewResponse.data;
            controls = controlsResponse.data;
          }
          if (view === "strategy") {
            const controlsResponse = await apiClient.get(`/instances/${me.instance_id}/controls`);
            controls = controlsResponse.data;
          }
          if (view === "challenges") {
            const controlsResponse = await apiClient.get(`/instances/${me.instance_id}/controls`);
            controls = controlsResponse.data;
          }
          if (view === "debrief") {
            const debriefResponse = await apiClient.get(`/instances/${me.instance_id}/debrief`);
            debrief = debriefResponse.data;
          }
        }
        if (active) setState({ status: "ready", me, instance, schedule, dashboard, platform, components, rollout, review, debrief, controls, hostPlatforms, error: "" });
      } catch (requestError) {
        if (!active) return;
        if (requestError.response?.status === 401 || requestError.response?.status === 403) {
          clearAccessToken();
          navigate("/login", { replace: true });
          return;
        }
        setState({ status: "error", me: null, instance: null, schedule: null, dashboard: null, platform: null, components: null, rollout: null, review: null, debrief: null, controls: null, hostPlatforms: null, error: requestError.response?.data?.detail || "The simulation context could not be loaded." });
      }
    }
    load();
    return () => { active = false; };
  }, [navigate, view]);

  if (state.status === "loading") return <main className="app-shell plain-state"><div className="loading-state"><div className="loading-spinner" /><span>Loading…</span></div></main>;
  if (state.status === "error") return <main className="app-shell plain-state"><h1>We could not open this simulation</h1><p role="alert">{state.error}</p></main>;

  const title = viewTitles[view] || "Dashboard";
  const activePath = view === "dashboard" ? "/" : view === "application-detail" ? "/applications" : `/${view}`;

  function renderView() {
    switch (view) {
      case "strategy":
        return <StrategyPage data={state.controls} instanceId={state.instance?.instance_id} />;
      case "infrastructure":
        return <InfrastructurePage platformData={state.platform} controlsData={state.controls} instanceId={state.instance?.instance_id} hostPlatforms={state.hostPlatforms} />;
      case "applications":
        return <ApplicationsPage data={state.components} instanceId={state.instance?.instance_id} hostPlatforms={state.hostPlatforms} />;
      case "application-detail":
        return <ApplicationDetailPage data={state.components} instanceId={state.instance?.instance_id} />;
      case "rollout":
        return <Rollout data={state.rollout} controlsData={state.controls} instanceId={state.instance?.instance_id} />;
      case "review":
        return <Review data={state.review} controlsData={state.controls} instanceId={state.instance?.instance_id} />;
      case "debrief":
        return <Debrief data={state.debrief} instanceId={state.instance?.instance_id} />;
      case "challenges":
        return <Controls data={state.controls} instanceId={state.instance?.instance_id} section="challenges" />;
      default:
        return <Dashboard data={state.dashboard} />;
    }
  }

  return (
    <AppShell me={state.me} instance={state.instance} schedule={state.schedule} dashboard={state.dashboard} activePath={activePath} pageTitle={title}>
      {renderView()}
    </AppShell>
  );
}
