import React, { useState } from "react";
import { analyze, exportExcel } from "../api";
import FilterPanel from "../components/FilterPanel";
import SummaryCards from "../components/SummaryCards";
import TopWordsChart from "../components/TopWordsChart";
import TopPhrasesChart from "../components/TopPhrasesChart";
import ClusterChart from "../components/ClusterChart";
import PhraseGroupsTable from "../components/PhraseGroupsTable";

const colors = {
  pageBg: "#f8fafc",
  cardBg: "#ffffff",
  softCardBg: "#fbfcfe",
  text: "#0f172a",
  muted: "#667085",
  border: "#e5e7eb",
  borderSoft: "#eef2f7",
  primary: "#2563eb",
  primarySoft: "#eff6ff",
  secondarySoft: "#f1f5f9",
  dangerBg: "#fef2f2",
  dangerBorder: "#fecaca",
  dangerText: "#dc2626",
  shadow: "0 10px 30px rgba(15, 23, 42, 0.06)",
};

const cardStyle = {
  background: colors.cardBg,
  border: `1px solid ${colors.border}`,
  borderRadius: 18,
  boxShadow: colors.shadow,
};

export default function DashboardPage({ auth, onLogout }) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  const handleAnalyze = async (payload) => {
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
    if (payload?.date_from && payload?.date_to && payload.date_from > payload.date_to) {
      setError("Date From cannot be after Date To");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const blob = await exportExcel(payload, auth.token);
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
    <div
      style={{
        minHeight: "100vh",
        background: colors.pageBg,
        padding: "28px 20px 40px",
        fontFamily:
          'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      }}
    >
      <div style={{ maxWidth: 1280, margin: "0 auto" }}>
        <div
          style={{
            ...cardStyle,
            padding: "22px 24px",
            marginBottom: 18,
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: 16,
              flexWrap: "wrap",
            }}
          >
            <div>
              <div
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  padding: "6px 12px",
                  borderRadius: 999,
                  background: colors.primarySoft,
                  color: colors.primary,
                  fontWeight: 800,
                  fontSize: 12,
                  letterSpacing: 0.3,
                  marginBottom: 10,
                }}
              >
                COMMUNICATION ANALYTICS
              </div>

              <h1
                style={{
                  margin: 0,
                  color: colors.text,
                  fontSize: 28,
                  lineHeight: 1.15,
                  fontWeight: 800,
                }}
              >
                NLP Dashboard
              </h1>

              <p
                style={{
                  margin: "8px 0 0",
                  color: colors.muted,
                  fontSize: 14,
                }}
              >
                Analyze multi-source communication trends, phrases, and clusters.
              </p>
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
                flexWrap: "wrap",
              }}
            >
              <div
                style={{
                  padding: "10px 14px",
                  borderRadius: 12,
                  background: "#f8fafc",
                  border: `1px solid ${colors.border}`,
                  color: colors.text,
                  fontSize: 14,
                  fontWeight: 600,
                }}
              >
                {auth?.name || "User"}{" "}
                <span style={{ color: colors.muted, fontWeight: 500 }}>
                  ({auth?.role || "Role"})
                </span>
              </div>

              <button
                onClick={onLogout}
                style={{
                  padding: "11px 16px",
                  borderRadius: 12,
                  border: `1px solid ${colors.border}`,
                  background: "#ffffff",
                  color: colors.text,
                  fontSize: 14,
                  fontWeight: 700,
                  cursor: "pointer",
                }}
              >
                Logout
              </button>
            </div>
          </div>
        </div>

        <div
          style={{
            ...cardStyle,
            padding: 18,
            marginBottom: 18,
          }}
        >
          <FilterPanel onAnalyze={handleAnalyze} onExport={handleExport} loading={loading} />
        </div>

        {error && (
          <div
            style={{
              marginBottom: 18,
              padding: "14px 16px",
              borderRadius: 14,
              background: colors.dangerBg,
              border: `1px solid ${colors.dangerBorder}`,
              color: colors.dangerText,
              fontSize: 14,
              lineHeight: 1.5,
              fontWeight: 600,
            }}
          >
            {error}
          </div>
        )}

        <div style={{ marginBottom: 18 }}>
          <SummaryCards data={data} />
        </div>

        {data && (
          <>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
                gap: 18,
                marginBottom: 18,
              }}
            >
              <div style={{ ...cardStyle, padding: 16 }}>
                <TopWordsChart data={data.top_words} />
              </div>

              <div style={{ ...cardStyle, padding: 16 }}>
                <TopPhrasesChart data={data.top_phrases} />
              </div>
            </div>

            <div style={{ ...cardStyle, padding: 16, marginBottom: 18 }}>
              <ClusterChart data={data.cluster_counts} />
            </div>

            <div style={{ ...cardStyle, padding: 16, marginBottom: 18 }}>
              <PhraseGroupsTable rows={data.phrase_groups} />
            </div>

            <div style={{ ...cardStyle, padding: 18 }}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  gap: 12,
                  flexWrap: "wrap",
                  marginBottom: 14,
                }}
              >
                <div>
                  <h3
                    style={{
                      margin: 0,
                      color: colors.text,
                      fontSize: 20,
                      fontWeight: 800,
                    }}
                  >
                    Sample Messages
                  </h3>
                  <p
                    style={{
                      margin: "6px 0 0",
                      color: colors.muted,
                      fontSize: 14,
                    }}
                  >
                    Preview of filtered records used in the analysis output.
                  </p>
                </div>

                <div
                  style={{
                    padding: "8px 12px",
                    borderRadius: 999,
                    background: "#f8fafc",
                    border: `1px solid ${colors.border}`,
                    color: colors.muted,
                    fontSize: 13,
                    fontWeight: 700,
                  }}
                >
                  {(data.sample_messages || []).length} rows
                </div>
              </div>

              <div
                style={{
                  overflowX: "auto",
                  border: `1px solid ${colors.border}`,
                  borderRadius: 14,
                }}
              >
                <table
                  style={{
                    width: "100%",
                    borderCollapse: "collapse",
                    minWidth: 980,
                    background: "#ffffff",
                  }}
                >
                  <thead>
                    <tr style={{ background: "#f8fafc" }}>
                      {["ID", "Source", "Sender", "Project", "Subject", "Cluster", "Text"].map(
                        (col) => (
                          <th
                            key={col}
                            style={{
                              textAlign: "left",
                              padding: "12px 14px",
                              borderBottom: `1px solid ${colors.border}`,
                              color: colors.text,
                              fontSize: 13,
                              fontWeight: 800,
                              whiteSpace: "nowrap",
                            }}
                          >
                            {col}
                          </th>
                        )
                      )}
                    </tr>
                  </thead>

                  <tbody>
                    {(data.sample_messages || []).map((r, idx) => (
                      <tr key={idx}>
                        <td
                          style={{
                            padding: "12px 14px",
                            borderBottom: `1px solid ${colors.borderSoft}`,
                            verticalAlign: "top",
                            fontSize: 14,
                            color: colors.text,
                          }}
                        >
                          {r.id}
                        </td>
                        <td
                          style={{
                            padding: "12px 14px",
                            borderBottom: `1px solid ${colors.borderSoft}`,
                            verticalAlign: "top",
                            fontSize: 14,
                            color: colors.text,
                            fontWeight: 600,
                          }}
                        >
                          {r.source}
                        </td>
                        <td
                          style={{
                            padding: "12px 14px",
                            borderBottom: `1px solid ${colors.borderSoft}`,
                            verticalAlign: "top",
                            fontSize: 14,
                            color: colors.text,
                          }}
                        >
                          {r.sender}
                        </td>
                        <td
                          style={{
                            padding: "12px 14px",
                            borderBottom: `1px solid ${colors.borderSoft}`,
                            verticalAlign: "top",
                            fontSize: 14,
                            color: colors.text,
                          }}
                        >
                          {r.project_id ?? ""}
                        </td>
                        <td
                          style={{
                            padding: "12px 14px",
                            borderBottom: `1px solid ${colors.borderSoft}`,
                            verticalAlign: "top",
                            fontSize: 14,
                            color: colors.text,
                            maxWidth: 220,
                          }}
                        >
                          {r.subject}
                        </td>
                        <td
                          style={{
                            padding: "12px 14px",
                            borderBottom: `1px solid ${colors.borderSoft}`,
                            verticalAlign: "top",
                            fontSize: 14,
                            color: colors.text,
                          }}
                        >
                          {r.cluster_id ?? ""}
                        </td>
                        <td
                          style={{
                            padding: "12px 14px",
                            borderBottom: `1px solid ${colors.borderSoft}`,
                            verticalAlign: "top",
                            fontSize: 14,
                            color: colors.muted,
                            lineHeight: 1.5,
                            minWidth: 320,
                          }}
                        >
                          {String(r.text || "").slice(0, 120)}
                          {String(r.text || "").length > 120 ? "..." : ""}
                        </td>
                      </tr>
                    ))}

                    {(!data.sample_messages || data.sample_messages.length === 0) && (
                      <tr>
                        <td
                          colSpan={7}
                          style={{
                            padding: 20,
                            textAlign: "center",
                            color: colors.muted,
                            fontSize: 14,
                          }}
                        >
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
    </div>
  );
}
