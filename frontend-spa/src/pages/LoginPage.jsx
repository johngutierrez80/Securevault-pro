import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginUser, registerUser } from "../api/auth";
import "./LoginPage.css";

export default function LoginPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [message, setMessage] = useState({ text: "", isError: true });

  function setMsg(text, isError = true) {
    setMessage({ text, isError });
  }

  function validate() {
    if (!username.trim() || !password.trim()) {
      setMsg("Credenciales incorrectas");
      return false;
    }
    return true;
  }

  async function handleLogin() {
    if (!validate()) return;
    try {
      const { ok, data } = await loginUser(username, password);
      if (ok) {
        localStorage.setItem("token", data.access_token);
        navigate("/dashboard");
      } else {
        setMsg("Credenciales incorrectas");
      }
    } catch {
      setMsg("No fue posible conectar con el servicio de autenticación.");
    }
  }

  async function handleRegister() {
    if (!validate()) return;
    try {
      const { ok } = await registerUser(username, password);
      if (ok) {
        setMsg("Usuario creado. Ahora puedes iniciar sesión.", false);
      } else {
        setMsg("Credenciales incorrectas");
      }
    } catch {
      setMsg("No fue posible conectar con el servicio de autenticación.");
    }
  }

  function handleForgotPassword() {
    setMsg("Función no disponible en esta versión académica.");
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
                  Usuario o Email
                </label>
                <div className="input-group">
                  <span className="input-group-text login-input-addon">
                    <i className="bi bi-person"></i>
                  </span>
                  <input
                    type="text"
                    className="form-control login-input"
                    placeholder="tu@correo.com o usuario"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
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
                    onClick={() => setShowPassword((v) => !v)}
                  >
                    <i
                      className={`bi ${showPassword ? "bi-eye-slash" : "bi-eye"}`}
                    ></i>
                  </button>
                </div>
              </div>

              <div className="d-flex justify-content-between align-items-center mb-4 small">
                <div className="form-check">
                  <input
                    className="form-check-input"
                    type="checkbox"
                    id="remember"
                    defaultChecked
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
