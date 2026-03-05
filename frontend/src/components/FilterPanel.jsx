import React, { useState } from "react";

export default function FilterPanel({ onAnalyze, onExport, loading }) {
  const [keywordsText, setKeywordsText] = useState("timeline, eta, risk, blocked, dependency, urgent");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [sourcesText, setSourcesText] = useState("gmail,outlook,teams,jira,ppt");
  const [fuzzyThreshold, setFuzzyThreshold] = useState(80);

  const buildPayload = () => ({
    keywords: keywordsText.split(",").map(s => s.trim()).filter(Boolean),
    date_from: dateFrom || null,
    date_to: dateTo || null,
    sources: sourcesText.split(",").map(s => s.trim()).filter(Boolean),
    include_numbers: true,
    include_symbols: true,
    include_ticket_ids: true,
    fuzzy_threshold: Number(fuzzyThreshold)
  });

  return (
    <div style={{ border: "1px solid #ddd", padding: 12, marginBottom: 16 }}>
      <h3>Filters</h3>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
        <div>
          <label>Keywords / Phrases (comma-separated)</label>
          <textarea
            rows={3}
            style={{ width: "100%" }}
            value={keywordsText}
            onChange={(e) => setKeywordsText(e.target.value)}
          />
        </div>
        <div>
          <label>Sources (comma-separated)</label>
          <input
            style={{ width: "100%" }}
            value={sourcesText}
            onChange={(e) => setSourcesText(e.target.value)}
          />
          <div style={{ marginTop: 10 }}>
            <label>Fuzzy Threshold</label>
            <input
              type="number"
              min="50"
              max="100"
              style={{ width: "100%" }}
              value={fuzzyThreshold}
              onChange={(e) => setFuzzyThreshold(e.target.value)}
            />
          </div>
        </div>
        <div>
          <label>Date From</label>
          <input type="date" style={{ width: "100%" }} value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
        </div>
        <div>
          <label>Date To</label>
          <input type="date" style={{ width: "100%" }} value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
        </div>
      </div>

      <div style={{ marginTop: 12 }}>
        <button onClick={() => onAnalyze(buildPayload())} disabled={loading} style={{ marginRight: 8 }}>
          {loading ? "Analyzing..." : "Analyze"}
        </button>
        <button onClick={() => onExport(buildPayload())} disabled={loading}>
          Export Excel
        </button>
      </div>
    </div>
  );
}