import React, { useState } from "react";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";

export default function App() {
  // Initialize state from localStorage so the session survives a browser refresh
  const [auth, setAuth] = useState(() => {
    const savedToken = localStorage.getItem("token");
    const savedUser = localStorage.getItem("user");
    
    // If both exist, we reconstruct the auth object; otherwise, start at Login
    if (savedToken && savedUser) {
      try {
        return { token: savedToken, user: JSON.parse(savedUser) };
      } catch (e) {
        console.error("Error parsing saved user:", e);
        return null;
      }
    }
    return null;
  });

  // This handler is passed to LoginPage to capture successful backend responses
  const handleLogin = (data) => {
    // 1. Persist to browser storage
    localStorage.setItem("token", data.token);
    localStorage.setItem("user", JSON.stringify({
      name: data.name,
      email: data.email,
      role: data.role
    }));
    
    // 2. Update React state to trigger the switch to DashboardPage
    setAuth({
      token: data.token,
      user: { name: data.name, email: data.email, role: data.role }
    });
  };

  const handleLogout = () => {
    // Clear everything to prevent unauthorized access on next load
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setAuth(null);
  };

  // Conditional Rendering: If no auth object exists, show the login screen
  if (!auth) {
    return <LoginPage onLogin={handleLogin} />;
  }

  // If auth exists, show the Dashboard and pass the token for API calls
  return <DashboardPage auth={auth} onLogout={handleLogout} />;
}