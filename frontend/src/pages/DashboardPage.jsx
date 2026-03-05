import React, { useState } from "react";
import { analyze, exportExcel } from "../api";
import FilterPanel from "../components/FilterPanel";
import SummaryCards from "../components/SummaryCards";
import TopWordsChart from "../components/TopWordsChart";
import TopPhrasesChart from "../components/TopPhrasesChart";
import ClusterChart from "../components/ClusterChart";
import PhraseGroupsTable from "../components/PhraseGroupsTable";

export default function DashboardPage({ auth, onLogout }) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  const handleAnalyze = async (payload) => {
    // Optional frontend validation
    if (payload?.date_from && payload?.date_to && payload.date_from > payload.date_to) {
      setError("Date From cannot be after Date To");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const res = await analyze(payload, auth.token);
      setData(res);
    } catch (err) {
      setError(err?.response?.data?.detail || "Analyze failed");
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (payload) => {
    // Optional frontend validation
    if (payload?.date_from && payload?.date_to && payload.date_from > payload.date_to) {
      setError("Date From cannot be after Date To");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const blob = await exportExcel(payload, auth.token);

      // Create a downloadable file in browser
      const url = window.URL.createObjectURL(new Blob([blob]));
      const a = document.createElement("a");
      a.href = url;
      a.download = "nlp_dashboard.xlsx";
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err?.response?.data?.detail || "Export failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 1200, margin: "20px auto", fontFamily: "Arial" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: 12,
          flexWrap: "wrap",
        }}
      >
        <h2 style={{ margin: 0 }}>NLP Dashboard</h2>
        <div>
          <span style={{ marginRight: 12 }}>
            {auth?.name} ({auth?.role})
          </span>
          <button onClick={onLogout}>Logout</button>
        </div>
      </div>

      <div style={{ marginTop: 12 }}>
        <FilterPanel onAnalyze={handleAnalyze} onExport={handleExport} loading={loading} />
      </div>

      {error && <p style={{ color: "red", marginTop: 8 }}>{error}</p>}

      <SummaryCards data={data} />

      {data && (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <TopWordsChart data={data.top_words} />
            <TopPhrasesChart data={data.top_phrases} />
          </div>

          <div style={{ marginTop: 12 }}>
            <ClusterChart data={data.cluster_counts} />
          </div>

          <PhraseGroupsTable rows={data.phrase_groups} />

          <div style={{ border: "1px solid #ddd", padding: 8, marginTop: 16 }}>
            <h4 style={{ marginTop: 0 }}>Sample Messages</h4>
            <div style={{ maxHeight: 300, overflow: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>ID</th>
                    <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>Source</th>
                    <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>Sender</th>
                    <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>Project</th>
                    <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>Subject</th>
                    <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>Cluster</th>
                    <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>Text</th>
                  </tr>
                </thead>
                <tbody>
                  {(data.sample_messages || []).map((r, idx) => (
                    <tr key={idx}>
                      <td style={{ borderBottom: "1px solid #f2f2f2", verticalAlign: "top" }}>{r.id}</td>
                      <td style={{ borderBottom: "1px solid #f2f2f2", verticalAlign: "top" }}>{r.source}</td>
                      <td style={{ borderBottom: "1px solid #f2f2f2", verticalAlign: "top" }}>{r.sender}</td>
                      <td style={{ borderBottom: "1px solid #f2f2f2", verticalAlign: "top" }}>{r.project_id ?? ""}</td>
                      <td style={{ borderBottom: "1px solid #f2f2f2", verticalAlign: "top" }}>{r.subject}</td>
                      <td style={{ borderBottom: "1px solid #f2f2f2", verticalAlign: "top" }}>{r.cluster_id ?? ""}</td>
                      <td style={{ borderBottom: "1px solid #f2f2f2", verticalAlign: "top" }}>
                        {String(r.text || "").slice(0, 120)}
                        {String(r.text || "").length > 120 ? "..." : ""}
                      </td>
                    </tr>
                  ))}
                  {(!data.sample_messages || data.sample_messages.length === 0) && (
                    <tr>
                      <td colSpan={7} style={{ padding: 8, color: "#666" }}>
                        No sample messages found for the selected filters.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}