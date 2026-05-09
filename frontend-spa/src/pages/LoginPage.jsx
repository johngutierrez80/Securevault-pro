import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  clearAuthSession,
  loginUser,
  persistAuthSession,
  registerUser,
  requestPasswordReset,
  resetPassword,
  storeUserProfile,
} from "../api/auth";
import "./LoginPage.css";

const LAST_LOGIN_EMAIL_KEY = "last_login_email";
const LAST_LOGIN_EMAIL_TS_KEY = "last_login_email_ts";
const LAST_LOGIN_EMAIL_TTL_MS = 60 * 60 * 1000;

function readBufferedEmail() {
  const email = localStorage.getItem(LAST_LOGIN_EMAIL_KEY) || "";
  const tsRaw = localStorage.getItem(LAST_LOGIN_EMAIL_TS_KEY);
  const ts = Number(tsRaw);

  if (!email || !Number.isFinite(ts)) {
    localStorage.removeItem(LAST_LOGIN_EMAIL_KEY);
    localStorage.removeItem(LAST_LOGIN_EMAIL_TS_KEY);
    return "";
  }

  const isExpired = Date.now() - ts > LAST_LOGIN_EMAIL_TTL_MS;
  if (isExpired) {
    localStorage.removeItem(LAST_LOGIN_EMAIL_KEY);
    localStorage.removeItem(LAST_LOGIN_EMAIL_TS_KEY);
    return "";
  }

  return email;
}

function writeBufferedEmail(emailValue) {
  localStorage.setItem(LAST_LOGIN_EMAIL_KEY, emailValue.trim().toLowerCase());
  localStorage.setItem(LAST_LOGIN_EMAIL_TS_KEY, String(Date.now()));
}

function isValidEmail(email) {
  return /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email.trim().toLowerCase());
}

function passwordStrength(password) {
  const value = password.trim();
  return [
    { label: "Al menos 10 caracteres", ok: value.length >= 10 },
    { label: "Una letra mayúscula", ok: /[A-Z]/.test(value) },
    { label: "Una letra minúscula", ok: /[a-z]/.test(value) },
    { label: "Un número", ok: /\d/.test(value) },
    { label: "Un símbolo", ok: /[^A-Za-z0-9]/.test(value) },
  ];
}

function joinIssues(issues) {
  return issues.join(" · ");
}

function secureRandomInt(max) {
  if (typeof window !== "undefined" && window.crypto?.getRandomValues) {
    const arr = new Uint32Array(1);
    window.crypto.getRandomValues(arr);
    return arr[0] % max;
  }
  return Math.floor(Math.random() * max);
}

function createStrongPassword(length = 20) {
  const uppercase = "ABCDEFGHJKLMNPQRSTUVWXYZ";
  const lowercase = "abcdefghijkmnopqrstuvwxyz";
  const numbers = "23456789";
  const symbols = "!@#$%^&*()-_=+[]{}";
  const all = uppercase + lowercase + numbers + symbols;

  const required = [
    uppercase[secureRandomInt(uppercase.length)],
    lowercase[secureRandomInt(lowercase.length)],
    numbers[secureRandomInt(numbers.length)],
    symbols[secureRandomInt(symbols.length)],
  ];

  while (required.length < length) {
    required.push(all[secureRandomInt(all.length)]);
  }

  for (let i = required.length - 1; i > 0; i -= 1) {
    const j = secureRandomInt(i + 1);
    [required[i], required[j]] = [required[j], required[i]];
  }

  return required.join("");
}

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState(() => readBufferedEmail());
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showPasswordHelp, setShowPasswordHelp] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [message, setMessage] = useState({ text: "", isError: true });
  const [showRecovery, setShowRecovery] = useState(false);
  const [recoveryEmail, setRecoveryEmail] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [showResetPassword, setShowResetPassword] = useState(false);
  const [recoveryMessage, setRecoveryMessage] = useState({
    text: "",
    isError: true,
  });
  const passwordHelpRef = useRef(null);

  const passwordIssues = passwordStrength(password);

  function setMsg(text, isError = true) {
    setMessage({ text, isError });
  }

  function setRecoveryMsg(text, isError = true) {
    setRecoveryMessage({ text, isError });
  }

  function handlePasswordHelpBlur() {
    requestAnimationFrame(() => {
      const activeElement = document.activeElement;
      if (!passwordHelpRef.current?.contains(activeElement)) {
        setShowPasswordHelp(false);
      }
    });
  }

  function handleSuggestStrongPassword() {
    const suggested = createStrongPassword();
    setPassword(suggested);
    setShowPassword(true);
    setShowPasswordHelp(true);
    setMsg(
      "Se generó una contraseña robusta. Puedes usarla para crear cuenta o cambiarla manualmente.",
      false,
    );
  }

  function validateLoginForm() {
    if (!isValidEmail(email)) {
      setMsg("Ingresa un correo electrónico válido.");
      return false;
    }
    if (!password.trim()) {
      setMsg("La contraseña es obligatoria.");
      return false;
    }
    return true;
  }

  async function handleLogin() {
    if (!validateLoginForm()) return;
    try {
      const { ok, data, status } = await loginUser(email, password);
      if (ok) {
        writeBufferedEmail(email);
        persistAuthSession(data.access_token, data.user, rememberMe);
        navigate("/boveda");
      } else {
        setMsg(
          data.detail ||
            (status === 401
              ? "Correo o contraseña inválidos."
              : "No se pudo iniciar sesión."),
        );
      }
    } catch {
      setMsg("No fue posible conectar con el servicio de autenticación.");
    }
  }

  async function handleRegister() {
    if (!isValidEmail(email)) {
      setMsg("Ingresa un correo electrónico válido.");
      return;
    }

    const weakIssues = passwordIssues.filter((item) => !item.ok).map((item) => item.label);
    if (weakIssues.length > 0) {
      setMsg(`La contraseña no cumple la política: ${joinIssues(weakIssues)}`);
      return;
    }

    try {
      const { ok, data, status } = await registerUser(email, password);
      if (ok) {
        writeBufferedEmail(email);
        if (data.user) {
          storeUserProfile(data.user, rememberMe);
        }
        setMsg("Usuario creado. Ahora puedes iniciar sesión.", false);
      } else {
        setMsg(
          data.detail ||
            (status === 400
              ? "El correo ya está registrado o la contraseña no cumple la política."
              : "No se pudo crear la cuenta."),
        );
      }
    } catch {
      setMsg("No fue posible conectar con el servicio de autenticación.");
    }
  }

  function handleForgotPassword() {
    setShowRecovery((value) => !value);
    setRecoveryMsg("");
    setRecoveryEmail(email);
    setResetToken("");
    setNewPassword("");
    setShowResetPassword(false);
  }

  async function handleRequestReset() {
    if (!isValidEmail(recoveryEmail)) {
      setRecoveryMsg("Ingresa un correo electrónico válido.");
      return;
    }

    try {
      const { ok, data, status } = await requestPasswordReset(recoveryEmail);
      if (ok) {
        setResetToken(data.reset_token || "");
        setRecoveryMsg(
          data.message || "Token de recuperación generado para esta versión.",
          false,
        );
      } else {
        setRecoveryMsg(
          data.detail ||
            (status === 404
              ? "No existe una cuenta asociada a ese correo."
              : "No se pudo generar el token de recuperación."),
        );
      }
    } catch {
      setRecoveryMsg("No fue posible conectar con el servicio de autenticación.");
    }
  }

  async function handleResetPassword() {
    if (!resetToken.trim()) {
      setRecoveryMsg("Debes ingresar el token de recuperación.");
      return;
    }
    if (!newPassword.trim()) {
      setRecoveryMsg("Debes ingresar la nueva contraseña.");
      return;
    }

    const weakIssues = passwordStrength(newPassword)
      .filter((item) => !item.ok)
      .map((item) => item.label);
    if (weakIssues.length > 0) {
      setRecoveryMsg(`La contraseña no cumple la política: ${joinIssues(weakIssues)}`);
      return;
    }

    try {
      const { ok, data } = await resetPassword(recoveryEmail, resetToken, newPassword);
      if (ok) {
        setRecoveryMsg(data.msg || "Contraseña actualizada correctamente.", false);
        setShowRecovery(false);
        setResetToken("");
        setNewPassword("");
        setPassword("");
        clearAuthSession();
        setMsg("Contraseña restablecida. Ya puedes iniciar sesión.", false);
      } else {
        setRecoveryMsg(data.detail || "No fue posible restablecer la contraseña.");
      }
    } catch {
      setRecoveryMsg("No fue posible conectar con el servicio de autenticación.");
    }
  }

  return (
    <div className="login-bg d-flex align-items-center">
      <div className="container login-container mx-auto px-3 py-5">
        <div className="text-center mb-5">
          <i className="bi bi-shield-lock-fill brand-logo"></i>
          <h2 className="fw-bold mt-2 mb-1 text-white">SecureVault</h2>
          <p className="text-secondary">Tu bóveda segura de contraseñas</p>
        </div>

        <div className="card p-4 p-md-5 shadow-lg">
          <div className="card-body">
            <h4 className="text-center mb-4 fw-semibold text-white">
              Iniciar Sesión
            </h4>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleLogin();
              }}
            >
              <div className="mb-4">
                <label className="form-label fw-medium text-white-50">
                  Correo electrónico
                </label>
                <div className="input-group">
                  <span className="input-group-text login-input-addon">
                    <i className="bi bi-person"></i>
                  </span>
                  <input
                    type="email"
                    className="form-control login-input"
                    placeholder="tu@correo.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    autoComplete="username"
                    maxLength={255}
                    autoFocus
                  />
                </div>
              </div>

              <div className="mb-4">
                <label className="form-label fw-medium text-white-50">
                  Contraseña
                </label>
                <div
                  className="password-help-anchor"
                  ref={passwordHelpRef}
                  onMouseEnter={() => setShowPasswordHelp(true)}
                  onMouseLeave={() => setShowPasswordHelp(false)}
                  onFocusCapture={() => setShowPasswordHelp(true)}
                  onBlurCapture={handlePasswordHelpBlur}
                >
                  <div className="input-group">
                    <span className="input-group-text login-input-addon">
                      <i className="bi bi-key"></i>
                    </span>
                    <input
                      type={showPassword ? "text" : "password"}
                      className="form-control login-input"
                      placeholder="••••••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      autoComplete="current-password"
                      maxLength={72}
                    />
                    <button
                      className="btn login-toggle-btn"
                      type="button"
                      onClick={() => setShowPassword((value) => !value)}
                    >
                      <i
                        className={`bi ${showPassword ? "bi-eye-slash" : "bi-eye"}`}
                      ></i>
                    </button>
                  </div>

                  {showPasswordHelp && (
                    <div className="password-help-popover" role="status" aria-live="polite">
                      <div className="small text-white-50 mb-2">
                        Requisitos recomendados para una contraseña robusta
                      </div>
                      <div className="row g-2">
                        {passwordIssues.map((item) => (
                          <div className="col-12" key={item.label}>
                            <div
                              className={`policy-item ${item.ok ? "policy-ok" : "policy-bad"}`}
                            >
                              <i
                                className={`bi ${item.ok ? "bi-check-circle-fill" : "bi-exclamation-circle-fill"}`}
                              ></i>
                              <span>{item.label}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                      <button
                        type="button"
                        className="btn btn-sm btn-outline-info mt-3"
                        onClick={handleSuggestStrongPassword}
                      >
                        Sugerir contraseña segura
                      </button>
                    </div>
                  )}
                </div>
              </div>

              <div className="d-flex justify-content-between align-items-center mb-4 small">
                <div className="form-check">
                  <input
                    className="form-check-input"
                    type="checkbox"
                    id="remember"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                  />
                  <label
                    className="form-check-label text-white-50"
                    htmlFor="remember"
                  >
                    Recordarme
                  </label>
                </div>
                <a
                  href="#"
                  className="text-link"
                  onClick={(e) => {
                    e.preventDefault();
                    handleForgotPassword();
                  }}
                >
                  ¿Olvidaste tu contraseña?
                </a>
              </div>

              <button type="submit" className="btn btn-login w-100 mb-3">
                <i className="bi bi-box-arrow-in-right me-2"></i> Iniciar Sesión
              </button>
            </form>

            <div className="text-center mt-4">
              <p className="text-secondary mb-2">¿Aún no tienes cuenta?</p>
              <button
                type="button"
                className="btn btn-outline-light btn-sm px-4"
                onClick={handleRegister}
              >
                Crear cuenta gratuita
              </button>
            </div>

            {message.text && (
              <div
                className={`mt-4 text-center fw-medium ${
                  message.isError ? "text-danger" : "text-success"
                }`}
              >
                {message.text}
              </div>
            )}

            {showRecovery && (
              <div className="recovery-panel mt-4 p-4">
                <h5 className="mb-3 text-white">Recuperar contraseña</h5>
                <p className="small text-white-50 mb-3">
                  En esta versión académica se genera un token temporal para
                  completar el cambio de contraseña sin correo saliente.
                </p>

                <div className="mb-3">
                  <label className="form-label fw-medium text-white-50">
                    Correo electrónico
                  </label>
                  <input
                    type="email"
                    className="form-control login-input"
                    value={recoveryEmail}
                    onChange={(e) => setRecoveryEmail(e.target.value)}
                    placeholder="tu@correo.com"
                  />
                </div>

                <div className="d-flex gap-2 mb-3 flex-wrap">
                  <button
                    type="button"
                    className="btn btn-outline-info"
                    onClick={handleRequestReset}
                  >
                    Solicitar token
                  </button>
                  <button
                    type="button"
                    className="btn btn-outline-light"
                    onClick={() => setShowRecovery(false)}
                  >
                    Cerrar
                  </button>
                </div>

                {resetToken && (
                  <>
                    <div className="mb-3">
                      <label className="form-label fw-medium text-white-50">
                        Token de recuperación
                      </label>
                      <textarea
                        className="form-control login-input recovery-token"
                        value={resetToken}
                        readOnly
                        rows={2}
                      />
                    </div>

                    <div className="mb-3">
                      <label className="form-label fw-medium text-white-50">
                        Nueva contraseña
                      </label>
                      <div className="input-group">
                        <input
                          type={showResetPassword ? "text" : "password"}
                          className="form-control login-input"
                          value={newPassword}
                          onChange={(e) => setNewPassword(e.target.value)}
                          placeholder="Nueva contraseña"
                        />
                        <button
                          className="btn login-toggle-btn"
                          type="button"
                          onClick={() => setShowResetPassword((value) => !value)}
                        >
                          <i
                            className={`bi ${showResetPassword ? "bi-eye-slash" : "bi-eye"}`}
                          ></i>
                        </button>
                      </div>
                    </div>

                    <button
                      type="button"
                      className="btn btn-login w-100"
                      onClick={handleResetPassword}
                    >
                      Restablecer contraseña
                    </button>
                  </>
                )}

                {recoveryMessage.text && (
                  <div
                    className={`mt-3 fw-medium ${
                      recoveryMessage.isError ? "text-danger" : "text-success"
                    }`}
                  >
                    {recoveryMessage.text}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        <div className="text-center mt-5 small text-secondary">
          <p>
            © 2026 SecureVault • Proyecto académico de Seguridad en Cloud y
            DevOps
          </p>
        </div>
      </div>
    </div>
  );
}
