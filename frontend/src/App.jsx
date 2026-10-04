import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import DevTokens from "./pages/DevTokens.jsx";
import Login from "./pages/Login.jsx";
import DevComponents from "./pages/DevComponents.jsx";
import Shell from "./pages/Shell.jsx";
import InstructorSetup from "./pages/InstructorSetup.jsx";
import InstructorRegistry from "./pages/InstructorRegistry.jsx";
import InstructorRoundControl from "./pages/InstructorRoundControl.jsx";
import InstructorMonitoring from "./pages/InstructorMonitoring.jsx";
import InstructorGrading from "./pages/InstructorGrading.jsx";

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
        <Route path="/strategy" element={<Shell view="strategy" />} />
        <Route path="/infrastructure" element={<Shell view="infrastructure" />} />
        <Route path="/applications" element={<Shell view="applications" />} />
        <Route path="/applications/:id" element={<Shell view="application-detail" />} />
        <Route path="/rollout" element={<Shell view="rollout" />} />
        <Route path="/review" element={<Shell view="review" />} />
        <Route path="/debrief" element={<Shell view="debrief" />} />
        <Route path="/challenges" element={<Shell view="challenges" />} />
        {/* Redirects from old routes */}
        <Route path="/platform" element={<Navigate to="/infrastructure" replace />} />
        <Route path="/services" element={<Navigate to="/infrastructure" replace />} />
        <Route path="/people" element={<Navigate to="/infrastructure" replace />} />
        <Route path="/security" element={<Navigate to="/infrastructure" replace />} />
        <Route path="/components" element={<Navigate to="/applications" replace />} />
        <Route path="/governance" element={<Navigate to="/rollout" replace />} />
        <Route path="/budget" element={<Navigate to="/review" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/instructor/setup" element={<InstructorSetup />} />
        <Route path="/instructor/registry" element={<InstructorRegistry />} />
        <Route path="/instructor/round-control" element={<InstructorRoundControl />} />
        <Route path="/instructor/monitoring" element={<InstructorMonitoring />} />
        <Route path="/instructor/grading" element={<InstructorGrading />} />
        <Route path="/_dev/tokens" element={<DevTokens />} />
        <Route path="/_dev/components" element={<DevComponents />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}
