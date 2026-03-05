import React from "react";

export default function SummaryCards({ data }) {
  if (!data) return null;

  return (
    <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
      <div style={{ border: "1px solid #ddd", padding: 12, minWidth: 160 }}>
        <div>Total Raw</div>
        <h2>{data.total_raw}</h2>
      </div>
      <div style={{ border: "1px solid #ddd", padding: 12, minWidth: 160 }}>
        <div>Total Filtered</div>
        <h2>{data.total_filtered}</h2>
      </div>
      <div style={{ border: "1px solid #ddd", padding: 12, minWidth: 160 }}>
        <div>Top Words</div>
        <h2>{data.top_words?.length || 0}</h2>
      </div>
      <div style={{ border: "1px solid #ddd", padding: 12, minWidth: 160 }}>
        <div>Clusters</div>
        <h2>{data.cluster_counts?.length || 0}</h2>
      </div>
    </div>
  );
}