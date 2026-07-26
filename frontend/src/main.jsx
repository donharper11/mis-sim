import React from "react";
import ReactDOM from "react-dom/client";
import { ConfigProvider } from "antd";
import "antd/dist/reset.css";
import "./i18n";
import "./styles/theme.css";
import App from "./App.jsx";

const rootStyles = getComputedStyle(document.documentElement);
const token = (name) => rootStyles.getPropertyValue(name).trim();

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: token("--accent-navy"),
          colorInfo: token("--accent-blue"),
          colorSuccess: token("--accent-green"),
          colorWarning: token("--accent-amber"),
          colorError: token("--accent-red"),
          colorText: token("--text-primary"),
          colorTextSecondary: token("--text-secondary"),
          colorBgLayout: token("--bg-content"),
          colorBgContainer: token("--bg-card"),
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

