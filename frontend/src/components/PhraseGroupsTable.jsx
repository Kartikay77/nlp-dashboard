import React from "react";

export default function PhraseGroupsTable({ rows }) {
  if (!rows || rows.length === 0) return null;

  return (
    <div style={{ border: "1px solid #ddd", borderRadius: "8px", padding: "16px", marginTop: "16px", backgroundColor: "#fff" }}>
      <h4 style={{ marginTop: 0, color: "#333" }}>Phrase Groups (Fuzzy Matches)</h4>
      <div style={{ maxHeight: "400px", overflow: "auto", border: "1px solid #eee" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "14px" }}>
          <thead style={{ position: "sticky", top: 0, backgroundColor: "#f9f9f9", zIndex: 1 }}>
            <tr>
              <th style={{ textAlign: "left", padding: "10px", borderBottom: "2px solid #ddd", width: "80px" }}>Group ID</th>
              <th style={{ textAlign: "left", padding: "10px", borderBottom: "2px solid #ddd" }}>Representative / Variations</th>
              <th style={{ textAlign: "right", padding: "10px", borderBottom: "2px solid #ddd", width: "100px" }}>Occurrences</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, idx) => {
              // Logic to check if this is the start of a new group for visual nesting
              const isFirstInGroup = idx === 0 || rows[idx - 1].group_id !== r.group_id;

              return (
                <tr 
                  key={idx} 
                  style={{ 
                    borderTop: isFirstInGroup ? "1px solid #eee" : "none",
                    backgroundColor: isFirstInGroup ? "rgba(0,0,0,0.02)" : "transparent"
                  }}
                >
                  <td style={{ padding: "8px 10px", color: "#888", fontWeight: isFirstInGroup ? "bold" : "normal" }}>
                    {isFirstInGroup ? `#${r.group_id}` : ""}
                  </td>
                  <td style={{ padding: "8px 10px" }}>
                    {isFirstInGroup ? (
                      <div style={{ fontWeight: "bold", color: "#2c3e50", marginBottom: "4px" }}>
                        {r.representative.toUpperCase()}
                      </div>
                    ) : null}
                    <div style={{ paddingLeft: isFirstInGroup ? "0" : "12px", color: isFirstInGroup ? "#555" : "#777", fontStyle: isFirstInGroup ? "normal" : "italic" }}>
                      • {r.phrase}
                    </div>
                  </td>
                  <td style={{ textAlign: "right", padding: "8px 10px", fontWeight: "bold", color: "#444" }}>
                    {r.count}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}