import React from "react";
import ReactDOM from "react-dom/client";
import { ConfigProvider } from "antd";
import "antd/dist/reset.css";
import "./i18n";
import "./styles/theme.css";
import App from "./App.jsx";

const rootStyles = getComputedStyle(document.documentElement);
const token = (name) => {
  const value = rootStyles.getPropertyValue(name).trim();
  if (!value) {
    throw new Error(`Missing design token: ${name}`);
  }
  return value;
};

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: token("--action-primary"),
          colorPrimaryHover: token("--action-primary-hover"),
          colorInfo: token("--status-info-marker"),
          colorSuccess: token("--status-ok-marker"),
          colorWarning: token("--status-warn-marker"),
          colorError: token("--status-danger-marker"),
          colorText: token("--text-primary"),
          colorTextSecondary: token("--text-secondary"),
          colorBgLayout: token("--surface-page"),
          colorBgContainer: token("--surface-card"),
          fontFamily: token("--font-body"),
          borderRadius: 0
        },
        components: {
          Button: {
            borderRadius: 0
          },
          Select: {
            borderRadius: 0
          },
          Table: {
            borderRadius: 0,
            headerBorderRadius: 0
          }
        }
      }}
    >
      <App />
    </ConfigProvider>
  </React.StrictMode>
);
