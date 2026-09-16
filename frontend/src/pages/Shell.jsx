/* eslint-disable react/prop-types */
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiClient, clearAccessToken } from "../api/client.js";
import AppShell from "../components/AppShell.jsx";
import Dashboard from "./Dashboard.jsx";
import Platform from "./Platform.jsx";
import Components from "./Components.jsx";
import Rollout from "./Rollout.jsx";
import Review from "./Review.jsx";
import Debrief from "./Debrief.jsx";
import Controls from "./Controls.jsx";

const controlViews = new Set(["strategy", "governance", "security", "services", "people", "challenges", "budget"]);

export default function Shell({ view = "dashboard" }) {
  const navigate = useNavigate();
  const [state, setState] = useState({ status: "loading", me: null, instance: null, schedule: null, dashboard: null, platform: null, components: null, rollout: null, review: null, debrief: null, controls: null, error: "" });

  useEffect(() => {
    let active = true;
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
        if (me.instance_id) {
          const instanceResponse = await apiClient.get(`/instances/${me.instance_id}`);
          instance = instanceResponse.data;
          const scheduleResponse = await apiClient.get(`/instances/${me.instance_id}/schedule`);
          schedule = scheduleResponse.data;
          const dashboardResponse = await apiClient.get(`/instances/${me.instance_id}/dashboard`);
          dashboard = dashboardResponse.data;
          if (view === "platform") {
            const platformResponse = await apiClient.get(`/instances/${me.instance_id}/platform`);
            platform = platformResponse.data;
          }
          if (view === "components") {
            const componentsResponse = await apiClient.get(`/instances/${me.instance_id}/components`);
            components = componentsResponse.data;
          }
          if (view === "rollout") {
            const rolloutResponse = await apiClient.get(`/instances/${me.instance_id}/rollout`);
            rollout = rolloutResponse.data;
          }
          if (view === "review") {
            const reviewResponse = await apiClient.get(`/instances/${me.instance_id}/review`);
            review = reviewResponse.data;
          }
          if (view === "debrief") {
            const debriefResponse = await apiClient.get(`/instances/${me.instance_id}/debrief`);
            debrief = debriefResponse.data;
          }
          if (controlViews.has(view)) {
            const controlsResponse = await apiClient.get(`/instances/${me.instance_id}/controls`);
            controls = controlsResponse.data;
          }
        }
        if (active) setState({ status: "ready", me, instance, schedule, dashboard, platform, components, rollout, review, debrief, controls, error: "" });
      } catch (requestError) {
        if (!active) return;
        if (requestError.response?.status === 401 || requestError.response?.status === 403) {
          clearAccessToken();
          navigate("/login", { replace: true });
          return;
        }
        setState({ status: "error", me: null, instance: null, schedule: null, dashboard: null, platform: null, components: null, rollout: null, review: null, debrief: null, controls: null, error: requestError.response?.data?.detail || "The simulation context could not be loaded." });
      }
    }
    load();
    return () => { active = false; };
  }, [navigate, view]);

  if (state.status === "loading") return <main className="app-shell plain-state"><p>Loading your simulation…</p></main>;
  if (state.status === "error") return <main className="app-shell plain-state"><h1>We could not open this simulation</h1><p role="alert">{state.error}</p></main>;
  const title = controlViews.has(view) ? view[0].toUpperCase() + view.slice(1) : view === "platform" ? "Platform" : view === "components" ? "Components" : view === "rollout" ? "Rollout" : view === "review" ? "Review" : view === "debrief" ? "Debrief" : "Dashboard";
  return <AppShell me={state.me} instance={state.instance} schedule={state.schedule} dashboard={state.dashboard} activePath={view === "dashboard" ? "/" : `/${view}`} pageTitle={title}>
    {controlViews.has(view) ? <Controls data={state.controls} instanceId={state.instance?.instance_id} section={view} /> : view === "platform" ? <Platform data={state.platform} instanceId={state.instance?.instance_id} /> : view === "components" ? <Components data={state.components} instanceId={state.instance?.instance_id} /> : view === "rollout" ? <Rollout data={state.rollout} instanceId={state.instance?.instance_id} /> : view === "review" ? <Review data={state.review} instanceId={state.instance?.instance_id} /> : view === "debrief" ? <Debrief data={state.debrief} instanceId={state.instance?.instance_id} /> : <Dashboard data={state.dashboard} />}
  </AppShell>;
}
