import axios from "axios";

// Dynamic API Base URL configuration
const getApiBaseUrl = (): string => {
  const backendHost = import.meta.env.BACKEND_HOST || "localhost";
  const backendPort = import.meta.env.BACKEND_PORT || "8000";
  const environment = import.meta.env.ENV || "development";

  if (environment === "production") {
    return import.meta.env.VITE_API_URL || "https://your-production-domain.com/";
  }

  if (backendHost === "0.0.0.0" || backendHost === "127.0.0.1") {
    return `http://localhost:${backendPort}/`;
  }
  
  return `http://${backendHost}:${backendPort}/`;
};

const API_BASE_URL = getApiBaseUrl();

console.log(`API Base URL: ${API_BASE_URL}`);
console.log(`Environment: ${import.meta.env.VITE_ENV || "development"}`);

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor for auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("auth_token");
      window.location.href = "/";
    }
    return Promise.reject(error);
  }
);

export default api;
