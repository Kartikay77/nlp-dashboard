import React, { useEffect, useState } from "react";
import { login, loginWithGoogle, loginWithMicrosoft } from "../api";

// Microsoft login popup helper (implicit token flow, simple demo approach)
function openMicrosoftLoginPopup(clientId, tenantId = "common") {
  return new Promise((resolve, reject) => {
    const redirectUri = `${window.location.origin}/ms-auth-callback.html`;
    const scope = encodeURIComponent("openid profile email User.Read Mail.Read");
    const authUrl =
      `https://login.microsoftonline.com/${tenantId}/oauth2/v2.0/authorize` +
      `?client_id=${encodeURIComponent(clientId)}` +
      `&response_type=token` +
      `&redirect_uri=${encodeURIComponent(redirectUri)}` +
      `&response_mode=fragment` +
      `&scope=${scope}` +
      `&state=12345`+
      `&prompt=select_account`;

    const w = 520;
    const h = 650;
    const left = window.screenX + (window.outerWidth - w) / 2;
    const top = window.screenY + (window.outerHeight - h) / 2;

    const popup = window.open(
      authUrl,
      "ms-login",
      `width=${w},height=${h},left=${left},top=${top}`
    );

    if (!popup) {
      reject(new Error("Popup blocked"));
      return;
    }

    const timer = setInterval(() => {
      if (popup.closed) {
        clearInterval(timer);
        reject(new Error("Login popup closed"));
      }
    }, 500);

    function onMessage(event) {
      if (event.origin !== window.location.origin) return;
      if (event.data?.type === "MS_AUTH_SUCCESS") {
        clearInterval(timer);
        window.removeEventListener("message", onMessage);
        popup.close();
        resolve(event.data.access_token);
      }
      if (event.data?.type === "MS_AUTH_ERROR") {
        clearInterval(timer);
        window.removeEventListener("message", onMessage);
        popup.close();
        reject(new Error(event.data.error || "Microsoft login failed"));
      }
    }

    window.addEventListener("message", onMessage);
  });
}

export default function LoginPage({ onLogin }) {
  const [username, setUsername] = useState("owner");
  const [password, setPassword] = useState("pass123");
  const [error, setError] = useState("");
  const [loadingGoogle, setLoadingGoogle] = useState(false);
  const [loadingMicrosoft, setLoadingMicrosoft] = useState(false);

  // Put these in .env later
  const googleClientId = process.env.REACT_APP_GOOGLE_CLIENT_ID || "";
  const microsoftClientId = process.env.REACT_APP_MICROSOFT_CLIENT_ID || "";

  useEffect(() => {
    // Load Google Identity Services script
    if (!googleClientId) return;

    const existing = document.getElementById("google-identity-script");
    if (existing) {
      initGoogle();
      return;
    }

    const script = document.createElement("script");
    script.id = "google-identity-script";
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = initGoogle;
    document.body.appendChild(script);

    function initGoogle() {
      if (!window.google?.accounts?.id || !googleClientId) return;

      window.google.accounts.id.initialize({
        client_id: googleClientId,
        callback: async (response) => {
          try {
            setError("");
            setLoadingGoogle(true);
            const data = await loginWithGoogle(response.credential); // ID token
            onLogin(data);
          } catch (err) {
            setError(err?.response?.data?.detail || "Google login failed");
          } finally {
            setLoadingGoogle(false);
          }
        }
      });

      const el = document.getElementById("googleSignInButton");
      if (el) {
        el.innerHTML = "";
        window.google.accounts.id.renderButton(el, {
          theme: "outline",
          size: "large",
          width: 300
        });
      }
    }
  }, [googleClientId, onLogin]);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const data = await login(username, password);
      onLogin(data);
    } catch (err) {
      setError(err?.response?.data?.detail || "Login failed");
    }
  };

  const handleMicrosoftLogin = async () => {
    try {
      if (!microsoftClientId) {
        setError("Missing VITE_MICROSOFT_CLIENT_ID");
        return;
      }
      setError("");
      setLoadingMicrosoft(true);

      const accessToken = await openMicrosoftLoginPopup(microsoftClientId);
      const data = await loginWithMicrosoft(accessToken);

      localStorage.setItem("token", data.token);
      onLogin(data);
    } catch (err) {
      console.error("Login failed:", err);
      setError(err?.response?.data?.detail || err.message || "Microsoft login failed");
    } finally {
      setLoadingMicrosoft(false);
    }
  };

  return (
    <div style={{ maxWidth: 420, margin: "60px auto", fontFamily: "Arial" }}>
      <h2>NLP Access Dashboard</h2>
      <p>Login (Lead / PM / Owner / Admin)</p>

      <form onSubmit={submit}>
        <div style={{ marginBottom: 10 }}>
          <label>Username</label>
          <input
            style={{ width: "100%", padding: 8 }}
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </div>

        <div style={{ marginBottom: 10 }}>
          <label>Password</label>
          <input
            type="password"
            style={{ width: "100%", padding: 8 }}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        <button type="submit" style={{ padding: "8px 12px", width: "100%" }}>
          Login
        </button>
      </form>

      <div style={{ margin: "16px 0", textAlign: "center", color: "#666" }}>or</div>

      <div style={{ display: "grid", gap: 10 }}>
        <div id="googleSignInButton" />
        {!googleClientId && (
          <small style={{ color: "#666" }}>
            Set <code>VITE_GOOGLE_CLIENT_ID</code> to enable Google login
          </small>
        )}

        <button
          type="button"
          onClick={handleMicrosoftLogin}
          disabled={loadingMicrosoft}
          style={{ padding: "10px 12px" }}
        >
          {loadingMicrosoft ? "Signing in..." : "Continue with Microsoft"}
        </button>
        {!microsoftClientId && (
          <small style={{ color: "#666" }}>
            Set <code>VITE_MICROSOFT_CLIENT_ID</code> to enable Microsoft login
          </small>
        )}
      </div>

      {error && <p style={{ color: "red", marginTop: 12 }}>{error}</p>}

      {loadingGoogle && <p style={{ color: "#555" }}>Signing in with Google...</p>}

      <hr />
      <small>Demo: lead1 / pm1 / owner / admin (password: pass123)</small>
    </div>
  );
}