import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

export async function login(username, password) {
  const res = await axios.post(`${API_BASE}/login`, { username, password });
  return res.data;
}

// Google OAuth login (send Google ID token to backend)
export async function loginWithGoogle(id_token) {
  const res = await axios.post(`${API_BASE}/login/google`, { id_token });
  return res.data;
}

// Microsoft OAuth login (send Microsoft access token to backend)
export async function loginWithMicrosoft(access_token) {
  const res = await axios.post(`${API_BASE}/login/microsoft`, { access_token });
  return res.data;
}

export async function analyze(payload, token) {
  const res = await axios.post(`${API_BASE}/analyze`, payload, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return res.data;
}

export async function exportExcel(payload, token) {
  const res = await axios.post(`${API_BASE}/export-excel`, payload, {
    headers: { Authorization: `Bearer ${token}` },
    responseType: "blob"
  });
  return res.data;
}

export function downloadExcel(blob, filename = "analysis_export.xlsx") {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

// Optional ingestion helpers if you want to use OAuth token directly for ingestion
export async function ingestGmail(payload, token) {
  const res = await axios.post(`${API_BASE}/ingest/gmail`, payload, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return res.data;
}

export async function ingestOutlook(payload, token) {
  const res = await axios.post(`${API_BASE}/ingest/outlook`, payload, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return res.data;
}

export async function ingestTeams(payload, token) {
  const res = await axios.post(`${API_BASE}/ingest/teams`, payload, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return res.data;
}

export async function ingestSharePointPpt(payload, token) {
  const res = await axios.post(`${API_BASE}/ingest/sharepoint-ppt`, payload, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return res.data;
}