import { BrowserRouter, Route, Routes } from "react-router-dom";
import DevTokens from "./pages/DevTokens.jsx";

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
        <Route path="/_dev/tokens" element={<DevTokens />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}

