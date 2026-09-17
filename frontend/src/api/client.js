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

export const getCurrentUser = () => apiClient.get("/auth/me");
export const listInstructorCourses = () => apiClient.get("/instructor/courses");
export const getCourseSetup = (courseId) => apiClient.get(`/instructor/courses/${courseId}/setup`);
export const listCasepacks = () => apiClient.get("/casepacks");
export const getSectionRoster = (sectionId) => apiClient.get(`/sections/${sectionId}/roster`);
export const getInstanceTeams = (instanceId) => apiClient.get(`/instances/${instanceId}/teams`);
