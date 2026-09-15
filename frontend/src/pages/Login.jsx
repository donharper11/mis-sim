import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiClient, storeAccessToken } from "../api/client.js";
import { useTranslation } from "react-i18next";

export default function Login() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [staff, setStaff] = useState(false);
  const [form, setForm] = useState({ identifier: "", password: "" });
  const [sections, setSections] = useState([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event, sectionId) {
    event?.preventDefault();
    setBusy(true);
    setError("");
    try {
      const payload = staff
        ? { email: form.identifier, password: form.password, ...(sectionId ? { section_id: sectionId } : {}) }
        : { student_id: form.identifier, password: form.password, ...(sectionId ? { section_id: sectionId } : {}) };
      const response = await apiClient.post(staff ? "/auth/staff-login" : "/auth/login", payload);
      storeAccessToken(response.data.access_token);
      await apiClient.get("/auth/me");
      navigate("/");
    } catch (requestError) {
      const data = requestError.response?.data;
      if (requestError.response?.status === 409 && data?.sections) {
        setSections(data.sections);
      } else if (requestError.response?.status === 403) {
        setError(data?.detail || t("login.forbidden"));
      } else {
        setError(data?.detail || t("login.invalid"));
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="app-shell login-page">
      <section className="login-card" aria-labelledby="login-title">
        <h1 id="login-title">{t("login.title")}</h1>
        <div className="login-mode" role="tablist" aria-label="Login type">
          <button type="button" className={!staff ? "active" : ""} onClick={() => { setStaff(false); setSections([]); }}>{t("login.student")}</button>
          <button type="button" className={staff ? "active" : ""} onClick={() => { setStaff(true); setSections([]); }}>{t("login.staff")}</button>
        </div>
        <form onSubmit={submit}>
          <label>{staff ? t("login.email") : t("login.student_id")}
            <input autoComplete={staff ? "email" : "username"} value={form.identifier} onChange={(e) => setForm({ ...form, identifier: e.target.value })} required />
          </label>
          <label>{t("login.password")}
            <input type="password" autoComplete="current-password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
          </label>
          <button type="submit" disabled={busy}>{t("login.submit")}</button>
        </form>
        {error && <p role="alert" className="login-error">{error}</p>}
        {sections.length > 0 && <div className="section-choices" aria-label={t("login.section")}>
          <p>{t("login.section")}</p>
          {sections.map((section) => <button type="button" key={section.section_id} onClick={(event) => submit(event, section.section_id)}>{section.section_name}</button>)}
        </div>}
      </section>
    </main>
  );
}
