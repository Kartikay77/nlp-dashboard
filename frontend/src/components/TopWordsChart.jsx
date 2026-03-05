import React from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from "recharts";

export default function TopWordsChart({ data }) {
  const rows = (data || []).slice(0, 15);
  return (
    <div style={{ width: "100%", height: 320, border: "1px solid #ddd", padding: 8 }}>
      <h4>Top Words</h4>
      <ResponsiveContainer width="100%" height="90%">
        <BarChart data={rows}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="word" angle={-25} textAnchor="end" height={70} />
          <YAxis />
          <Tooltip />
          <Bar dataKey="count" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}