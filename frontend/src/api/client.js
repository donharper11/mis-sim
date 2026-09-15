import axios from "axios";

export const apiClient = axios.create({
  baseURL: "/api"
});

apiClient.interceptors.request.use((config) => {
  const token = window.sessionStorage.getItem("mis_sim.access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export function storeAccessToken(token) {
  window.sessionStorage.setItem("mis_sim.access_token", token);
}

export function clearAccessToken() {
  window.sessionStorage.removeItem("mis_sim.access_token");
}
