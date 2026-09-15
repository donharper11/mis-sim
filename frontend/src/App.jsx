import { BrowserRouter, Route, Routes } from "react-router-dom";
import DevTokens from "./pages/DevTokens.jsx";
import Login from "./pages/Login.jsx";
import DevComponents from "./pages/DevComponents.jsx";
import Shell from "./pages/Shell.jsx";

function NotFound() {
  return (
    <main className="app-shell">
      <section className="plain-state">
        <h1>404</h1>
        <p>Page not found.</p>
      </section>
    </main>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Shell />} />
        <Route path="/platform" element={<Shell view="platform" />} />
        <Route path="/components" element={<Shell view="components" />} />
        <Route path="/rollout" element={<Shell view="rollout" />} />
        <Route path="/login" element={<Login />} />
        <Route path="/_dev/tokens" element={<DevTokens />} />
        <Route path="/_dev/components" element={<DevComponents />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}
