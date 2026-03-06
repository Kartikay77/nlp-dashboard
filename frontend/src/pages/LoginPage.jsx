import React, { useEffect, useState } from "react";
import { login, loginWithGoogle, loginWithMicrosoft } from "../api";

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
      `&state=12345` +
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

const colors = {
  pageBg: "#f8fafc",
  cardBg: "#ffffff",
  primary: "#2563eb",
  primaryHover: "#1d4ed8",
  text: "#0f172a",
  muted: "#667085",
  border: "#d0d5dd",
  borderSoft: "#e4e7ec",
  danger: "#dc2626",
  inputBg: "#ffffff",
  badgeBg: "#eff6ff",
  badgeText: "#2563eb",
  buttonSoftHover: "#f9fafb",
  shadow: "0 18px 40px rgba(15, 23, 42, 0.08)",
  focusRing: "0 0 0 4px rgba(37, 99, 235, 0.12)",
};

export default function LoginPage({ onLogin }) {
  const [username, setUsername] = useState("owner");
  const [password, setPassword] = useState("pass123");
  const [error, setError] = useState("");
  const [loadingGoogle, setLoadingGoogle] = useState(false);
  const [loadingMicrosoft, setLoadingMicrosoft] = useState(false);
  const [loadingLogin, setLoadingLogin] = useState(false);
  const [focusedField, setFocusedField] = useState("");

  const googleClientId = process.env.REACT_APP_GOOGLE_CLIENT_ID || "";
  const microsoftClientId = process.env.REACT_APP_MICROSOFT_CLIENT_ID || "";

  useEffect(() => {
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
            const data = await loginWithGoogle(response.credential);
            onLogin(data);
          } catch (err) {
            setError(err?.response?.data?.detail || "Google login failed");
          } finally {
            setLoadingGoogle(false);
          }
        },
      });

      const el = document.getElementById("googleSignInButton");
      if (el) {
        el.innerHTML = "";
        window.google.accounts.id.renderButton(el, {
          theme: "outline",
          size: "large",
          width: 300,
        });
      }
    }
  }, [googleClientId, onLogin]);

  const submit = async (e) => {
    e.preventDefault();
    setError("");

    try {
      setLoadingLogin(true);
      const data = await login(username, password);
      onLogin(data);
    } catch (err) {
      setError(err?.response?.data?.detail || "Login failed");
    } finally {
      setLoadingLogin(false);
    }
  };

  const handleMicrosoftLogin = async () => {
    try {
      if (!microsoftClientId) {
        setError("Missing REACT_APP_MICROSOFT_CLIENT_ID");
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
      setError(
        err?.response?.data?.detail ||
          err.message ||
          "Microsoft login failed"
      );
    } finally {
      setLoadingMicrosoft(false);
    }
  };

  const inputStyle = (fieldName) => ({
    width: "100%",
    padding: "14px 16px",
    borderRadius: 12,
    border:
      focusedField === fieldName
        ? `1px solid ${colors.primary}`
        : `1px solid ${colors.border}`,
    background: colors.inputBg,
    boxSizing: "border-box",
    fontSize: 16,
    color: colors.text,
    outline: "none",
    boxShadow: focusedField === fieldName ? colors.focusRing : "none",
    transition: "all 0.18s ease",
  });

  const disabled = loadingLogin || loadingGoogle || loadingMicrosoft;

  return (
    <div
      style={{
        minHeight: "100vh",
        background: colors.pageBg,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 24,
        fontFamily:
          'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: 470,
          background: colors.cardBg,
          border: `1px solid ${colors.borderSoft}`,
          borderRadius: 24,
          boxShadow: colors.shadow,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: 6,
            background: colors.primary,
          }}
        />

        <div style={{ padding: 32 }}>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              padding: "8px 16px",
              borderRadius: 999,
              background: colors.badgeBg,
              color: colors.badgeText,
              fontWeight: 800,
              fontSize: 13,
              letterSpacing: 0.3,
              marginBottom: 20,
            }}
          >
            COMMUNICATION ANALYTICS
          </div>

          <h1
            style={{
              margin: 0,
              color: colors.text,
              fontSize: 34,
              lineHeight: 1.12,
              fontWeight: 800,
            }}
          >
            NLP Access Dashboard
          </h1>

          <p
            style={{
              marginTop: 16,
              marginBottom: 28,
              color: colors.muted,
              fontSize: 16,
              lineHeight: 1.6,
            }}
          >
            Role-based access for Lead, PM, Owner, and Admin users across
            Gmail, Outlook, Teams, Jira, and PPT insights.
          </p>

          <form onSubmit={submit}>
            <div style={{ marginBottom: 18 }}>
              <label
                style={{
                  display: "block",
                  marginBottom: 8,
                  fontSize: 14,
                  fontWeight: 700,
                  color: "#344054",
                }}
              >
                Username
              </label>
              <input
                style={inputStyle("username")}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                onFocus={() => setFocusedField("username")}
                onBlur={() => setFocusedField("")}
                autoComplete="username"
                placeholder="Enter your username"
              />
            </div>

            <div style={{ marginBottom: 22 }}>
              <label
                style={{
                  display: "block",
                  marginBottom: 8,
                  fontSize: 14,
                  fontWeight: 700,
                  color: "#344054",
                }}
              >
                Password
              </label>
              <input
                type="password"
                style={inputStyle("password")}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onFocus={() => setFocusedField("password")}
                onBlur={() => setFocusedField("")}
                autoComplete="current-password"
                placeholder="Enter your password"
              />
            </div>

            <button
              type="submit"
              disabled={disabled}
              style={{
                width: "100%",
                padding: "15px 18px",
                borderRadius: 14,
                border: "none",
                background: colors.primary,
                color: "#ffffff",
                fontSize: 17,
                fontWeight: 800,
                cursor: disabled ? "not-allowed" : "pointer",
                opacity: disabled ? 0.75 : 1,
                transition: "all 0.18s ease",
              }}
              onMouseOver={(e) => {
                if (!disabled) e.currentTarget.style.background = colors.primaryHover;
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.background = colors.primary;
              }}
            >
              {loadingLogin ? "Signing in..." : "Login"}
            </button>
          </form>

          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 16,
              margin: "24px 0 18px",
              color: colors.muted,
            }}
          >
            <div
              style={{
                height: 1,
                flex: 1,
                background: colors.borderSoft,
              }}
            />
            <span style={{ fontSize: 14, fontWeight: 600 }}>or continue with</span>
            <div
              style={{
                height: 1,
                flex: 1,
                background: colors.borderSoft,
              }}
            />
          </div>

          <div style={{ display: "grid", gap: 14 }}>
            <div
              style={{
                display: "flex",
                justifyContent: "center",
                minHeight: 44,
              }}
            >
              <div id="googleSignInButton" />
            </div>

            {!googleClientId && (
              <small style={{ color: colors.muted, textAlign: "center" }}>
                Set <code>REACT_APP_GOOGLE_CLIENT_ID</code> to enable Google login
              </small>
            )}

            <button
              type="button"
              onClick={handleMicrosoftLogin}
              disabled={disabled}
              style={{
                width: "100%",
                padding: "14px 16px",
                borderRadius: 14,
                border: `1px solid ${colors.border}`,
                background: "#ffffff",
                color: colors.text,
                fontSize: 16,
                fontWeight: 700,
                cursor: disabled ? "not-allowed" : "pointer",
                opacity: disabled ? 0.75 : 1,
                transition: "all 0.18s ease",
              }}
              onMouseOver={(e) => {
                if (!disabled) e.currentTarget.style.background = colors.buttonSoftHover;
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.background = "#ffffff";
              }}
            >
              {loadingMicrosoft ? "Signing in..." : "Continue with Microsoft"}
            </button>

            {!microsoftClientId && (
              <small style={{ color: colors.muted, textAlign: "center" }}>
                Set <code>REACT_APP_MICROSOFT_CLIENT_ID</code> to enable Microsoft login
              </small>
            )}
          </div>

          {error && (
            <p
              style={{
                marginTop: 16,
                marginBottom: 0,
                padding: "12px 14px",
                borderRadius: 12,
                background: "#fef2f2",
                border: "1px solid #fecaca",
                color: colors.danger,
                fontSize: 14,
                lineHeight: 1.5,
              }}
            >
              {error}
            </p>
          )}

          {loadingGoogle && (
            <p
              style={{
                color: colors.muted,
                marginTop: 14,
                marginBottom: 0,
                fontSize: 14,
              }}
            >
              Signing in with Google...
            </p>
          )}

          <div
            style={{
              marginTop: 28,
              paddingTop: 18,
              borderTop: `1px solid ${colors.borderSoft}`,
              color: colors.muted,
              fontSize: 13.5,
              lineHeight: 1.6,
              textAlign: "left",
            }}
          >
            Demo: <strong>lead1</strong>, <strong>pm1</strong>, <strong>owner</strong>,{" "}
            <strong>admin</strong> · Password: <strong>pass123</strong>
          </div>
        </div>
      </div>
    </div>
  );
}
