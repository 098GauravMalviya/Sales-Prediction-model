// api.js — central API service
// Place this in src/api.js alongside your components

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const handleResponse = async (res) => {
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "API error");
  return data;
};

// ── Auth ─────────────────────────────────────────────────────────────
export const loginUser = (email, password) =>
  fetch(`${BASE_URL}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: email, password }),
  }).then(handleResponse);

export const signupUser = (email, password, fullName) =>
  fetch(`${BASE_URL}/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: email, password, full_name: fullName }),
  }).then(handleResponse);

// ── Prediction ────────────────────────────────────────────────────────
export const predictSales = (params) =>
  fetch(`${BASE_URL}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  }).then(handleResponse);

// ── Forecast ─────────────────────────────────────────────────────────
export const getForecast = (days = 90) =>
  fetch(`${BASE_URL}/forecast?days=${days}`).then(handleResponse);

// ── Analytics ────────────────────────────────────────────────────────
export const getHolidayAnalytics  = ()         => fetch(`${BASE_URL}/analytics/holidays`).then(handleResponse);
export const getCommodityAnalytics = (name)    => fetch(`${BASE_URL}/analytics/commodity/${name}`).then(handleResponse);
export const getMacroAnalytics     = ()         => fetch(`${BASE_URL}/analytics/macro`).then(handleResponse);
export const getStockAnalytics     = (ticker)  => fetch(`${BASE_URL}/analytics/stock/${ticker}`).then(handleResponse);

// ── Health ────────────────────────────────────────────────────────────
export const checkHealth = () => fetch(`${BASE_URL}/health`).then(handleResponse);