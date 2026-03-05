import React from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from "recharts";

export default function TopPhrasesChart({ data }) {
  const rows = (data || []).slice(0, 10);
  return (
    <div style={{ width: "100%", height: 320, border: "1px solid #ddd", padding: 8 }}>
      <h4>Top Phrases</h4>
      <ResponsiveContainer width="100%" height="90%">
        <BarChart data={rows}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="phrase" angle={-20} textAnchor="end" height={90} interval={0} />
          <YAxis />
          <Tooltip />
          <Bar dataKey="count" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}