import React from "react";
import { PieChart, Pie, Tooltip, ResponsiveContainer, Cell } from "recharts";

export default function ClusterChart({ data }) {
  const rows = (data || []).map(r => ({ name: `Cluster ${r.cluster_id}`, value: r.count }));
  const colors = ["#8884d8", "#82ca9d", "#ffc658", "#ff7f7f", "#8dd1e1", "#d0ed57", "#a4de6c"];

  return (
    <div style={{ width: "100%", height: 320, border: "1px solid #ddd", padding: 8 }}>
      <h4>Cluster Sizes</h4>
      <ResponsiveContainer width="100%" height="90%">
        <PieChart>
          <Pie data={rows} dataKey="value" nameKey="name" outerRadius={100} label>
            {rows.map((_, i) => <Cell key={i} fill={colors[i % colors.length]} />)}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}