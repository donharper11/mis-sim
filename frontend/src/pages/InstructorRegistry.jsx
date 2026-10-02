import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import AppShell from "../components/AppShell.jsx";
import { apiClient, getCurrentUser, listCasepacks, clearAccessToken } from "../api/client.js";

function requestError(error) {
  return error.response?.data?.detail || "The registry could not complete that action.";
}

function ValidationBadge({ errors, warnings }) {
  if (errors > 0) return <span className="badge badge--error">Errors: {errors}</span>;
  if (warnings > 0) return <span className="badge badge--warn">Warnings: {warnings}</span>;
  return <span className="badge badge--ok">Valid</span>;
}

export default function InstructorRegistry() {
  const navigate = useNavigate();
  const [state, setState] = useState({ loading: true, me: null, packs: [], error: "", notice: "" });
  const [registerKey, setRegisterKey] = useState("");
  const [showRegister, setShowRegister] = useState(false);
  const [selectedPack, setSelectedPack] = useState(null);
  const [validation, setValidation] = useState(null);
  const [instances, setInstances] = useState([]);
  const [registering, setRegistering] = useState(false);

  const load = useCallback(async () => {
    try {
      const [meResponse, packsResponse] = await Promise.all([getCurrentUser(), listCasepacks()]);
      if (meResponse.data.role !== "admin") {
        setState((prev) => ({ ...prev, loading: false, me: meResponse.data, error: "Admin access required." }));
        return;
      }
      setState((prev) => ({ ...prev, loading: false, me: meResponse.data, packs: packsResponse.data, error: "" }));
    } catch (error) {
      if ([401, 403].includes(error.response?.status)) {
        clearAccessToken();
        navigate("/login", { replace: true });
        return;
      }
      setState((prev) => ({ ...prev, loading: false, error: requestError(error) }));
    }
  }, [navigate]);

  useEffect(() => { load(); }, [load]);

  async function registerPack(event) {
    event.preventDefault();
    if (!registerKey.trim()) return;
    setRegistering(true);
    try {
      await apiClient.post("/admin/casepacks/register", { pack_key: registerKey.trim() });
      setState((prev) => ({ ...prev, notice: "Pack registered.", error: "" }));
      setRegisterKey("");
      setShowRegister(false);
      await load();
    } catch (error) {
      setState((prev) => ({ ...prev, error: requestError(error), notice: "" }));
    } finally {
      setRegistering(false);
    }
  }

  async function selectPack(pack) {
    setSelectedPack(pack);
    setValidation(null);
    setInstances([]);
    try {
      const [valRes, instRes] = await Promise.all([
        apiClient.get(`/admin/casepacks/${pack.pack_key}/${pack.pack_version}/validation`),
        apiClient.get(`/admin/casepacks/${pack.pack_key}/${pack.pack_version}/instances`),
      ]);
      setValidation(valRes.data);
      setInstances(instRes.data);
    } catch (error) {
      setState((prev) => ({ ...prev, error: requestError(error) }));
    }
  }

  async function deregisterPack() {
    if (!selectedPack) return;
    if (!window.confirm(`Deregister ${selectedPack.pack_key} ${selectedPack.pack_version}?`)) return;
    try {
      await apiClient.delete(`/admin/casepacks/${selectedPack.pack_key}/${selectedPack.pack_version}`);
      setState((prev) => ({ ...prev, notice: "Pack deregistered.", error: "" }));
      setSelectedPack(null);
      setValidation(null);
      setInstances([]);
      await load();
    } catch (error) {
      setState((prev) => ({ ...prev, error: requestError(error), notice: "" }));
    }
  }

  if (state.loading) return <main className="app-shell plain-state"><p>Loading registry...</p></main>;
  if (state.me && state.me.role !== "admin") {
    return <main className="app-shell plain-state"><p>Admin access required.</p></main>;
  }

  return (
    <AppShell me={state.me} activePath="/instructor/registry" pageTitle="Casepack registry">
      <div className="instructor-workspace">
        <header className="page-header">
          <p className="eyebrow">M5.6</p>
          <h2>Casepack registry management</h2>
          <p className="page-intro">Register on-disk packs, view validation reports, and manage pack lifecycle.</p>
        </header>
        {state.error && <p className="workspace-message workspace-message--error" role="alert">{state.error}</p>}
        {state.notice && <p className="workspace-message workspace-message--ok" role="status">{state.notice}</p>}

        <section className="setup-card" aria-labelledby="registry-heading">
          <div className="setup-card__heading">
            <h3 id="registry-heading">Registered packs</h3>
            <button type="button" onClick={() => setShowRegister(!showRegister)}>Register pack</button>
          </div>
          {showRegister && (
            <form className="setup-inline-form" onSubmit={registerPack}>
              <input
                aria-label="Pack key"
                placeholder="Pack key (e.g. riverside_grocery)"
                value={registerKey}
                onChange={(e) => setRegisterKey(e.target.value)}
                required
              />
              <button type="submit" disabled={registering}>{registering ? "Registering..." : "Register"}</button>
              <button type="button" onClick={() => setShowRegister(false)}>Cancel</button>
            </form>
          )}
          {state.packs.length === 0 ? (
            <p className="muted-copy">No packs registered.</p>
          ) : (
            <div className="setup-table-wrap">
              <table className="setup-table">
                <thead>
                  <tr>
                    <th>Pack key</th>
                    <th>Version</th>
                    <th>Display name</th>
                    <th>Rounds</th>
                    <th>Validation</th>
                  </tr>
                </thead>
                <tbody>
                  {state.packs.map((pack) => (
                    <tr
                      key={`${pack.pack_key}@${pack.pack_version}`}
                      onClick={() => selectPack(pack)}
                      style={{ cursor: "pointer" }}
                      className={selectedPack?.pack_key === pack.pack_key && selectedPack?.pack_version === pack.pack_version ? "setup-table__row--selected" : ""}
                    >
                      <td>{pack.pack_key}</td>
                      <td>{pack.pack_version}</td>
                      <td>{pack.display_name}</td>
                      <td>{pack.rounds}</td>
                      <td><ValidationBadge errors={pack.errors?.length || 0} warnings={pack.warnings?.length || 0} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {selectedPack && (
          <section className="setup-card" aria-labelledby="detail-heading">
            <div className="setup-card__heading">
              <h3 id="detail-heading">{selectedPack.display_name} {selectedPack.pack_version}</h3>
              <button type="button" onClick={deregisterPack} disabled={instances.length > 0}>
                {instances.length > 0 ? "Bound (cannot deregister)" : "Deregister"}
              </button>
            </div>
            <dl className="setup-facts">
              <div><dt>Pack key</dt><dd>{selectedPack.pack_key}</dd></div>
              <div><dt>Version</dt><dd>{selectedPack.pack_version}</dd></div>
              <div><dt>Digest</dt><dd className="mono-copy">{selectedPack.pack_digest}</dd></div>
              <div><dt>Vertical</dt><dd>{selectedPack.vertical}</dd></div>
              <div><dt>Rounds</dt><dd>{selectedPack.rounds}</dd></div>
            </dl>

            {validation && (
              <>
                <h4>Validation report</h4>
                <p>Exit code: {validation.exit_code} | Errors: {(validation.errors || []).length} | Warnings: {(validation.warnings || []).length}</p>
                {(validation.findings || []).length > 0 ? (
                  <div className="setup-table-wrap">
                    <table className="setup-table">
                      <thead><tr><th>Severity</th><th>Code</th><th>Message</th><th>File</th></tr></thead>
                      <tbody>
                        {validation.findings.map((f, i) => (
                          <tr key={i}>
                            <td><span className={`badge badge--${f.severity === "ERROR" ? "error" : f.severity === "WARN" ? "warn" : "info"}`}>{f.severity}</span></td>
                            <td>{f.code}</td>
                            <td>{f.message}</td>
                            <td>{f.file}{f.line ? `:${f.line}` : ""}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="muted-copy">No findings.</p>
                )}
              </>
            )}

            <h4>Bound instances ({instances.length})</h4>
            {instances.length === 0 ? (
              <p className="muted-copy">No instances bound to this pack version.</p>
            ) : (
              <div className="setup-table-wrap">
                <table className="setup-table">
                  <thead><tr><th>Instance ID</th><th>Section ID</th><th>Status</th><th>Round</th></tr></thead>
                  <tbody>
                    {instances.map((inst) => (
                      <tr key={inst.instance_id}>
                        <td>{inst.instance_id}</td>
                        <td>{inst.section_id}</td>
                        <td>{inst.status}</td>
                        <td>{inst.current_round} / {inst.total_rounds}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        )}
      </div>
    </AppShell>
  );
}
