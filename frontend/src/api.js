import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
});

// Attach the saved token to every outgoing request, if we have one.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("tokenwise_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// If the server says the session is dead, clear it and send the user
// back to the login page instead of showing a confusing error.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("tokenwise_token");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export function login(username, password) {
  return api.post("/api/auth/login", { username, password });
}

export function guestLogin() {
  return api.post("/api/auth/guest");
}

export function askQuestion(question) {
  return api.post("/api/ask", { question });
}

export function getStats() {
  return api.get("/api/stats");
}

// Pull a readable message out of whatever shape the error has -
// network failure, validation error, or a backend detail string.
export function getErrorMessage(error) {
  if (error.response?.data?.detail) {
    return error.response.data.detail;
  }
  if (error.code === "ECONNABORTED") {
    return "The request took too long and timed out. Try again.";
  }
  if (!error.response) {
    return "Can't reach the server. Check your connection and try again.";
  }
  return "Something went wrong. Try again.";
}

export default api;