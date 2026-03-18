import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  getSecrets,
  saveSecret,
  updateSecret,
  deleteSecret,
} from "../api/vault";
import "./DashboardPage.css";

function PasswordCell({ password }) {
  const [visible, setVisible] = useState(false);
  return (
    <div className="input-group input-group-sm vault-pass-group">
      <span className="input-group-text">
        <i className="bi bi-key"></i>
      </span>
      <input
        className="form-control password-cell"
        type={visible ? "text" : "password"}
        value={password}
        readOnly
        onChange={() => {}}
      />
      <button
        className="btn btn-outline-secondary"
        type="button"
        title="Mostrar u ocultar contraseña"
        onClick={() => setVisible((v) => !v)}
      >
        <i className={`bi ${visible ? "bi-eye-slash" : "bi-eye"}`}></i>
      </button>
    </div>
  );
}

function EditModal({ secret, onClose, onSave }) {
  const [site, setSite] = useState(secret.site);
  const [password, setPassword] = useState(secret.password);
  const [loading, setLoading] = useState(false);

  async function handleSave() {
    if (!site.trim() || !password.trim()) return;
    setLoading(true);
    await onSave(secret.id, site, password);
    setLoading(false);
  }

  return (
    <div className="edit-backdrop" onClick={onClose}>
      <div className="edit-dialog" onClick={(e) => e.stopPropagation()}>
        <div className="card p-4">
          <h5 className="mb-3">Editar secreto</h5>
          <div className="mb-3">
            <label className="form-label fw-medium">Sitio / Aplicación</label>
            <input
              className="form-control"
              value={site}
              onChange={(e) => setSite(e.target.value)}
              autoFocus
            />
          </div>
          <div className="mb-3">
            <label className="form-label fw-medium">Contraseña</label>
            <input
              className="form-control"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <div className="d-flex gap-2 justify-content-end">
            <button className="btn btn-secondary" onClick={onClose}>
              Cancelar
            </button>
            <button
              className="btn btn-warning"
              onClick={handleSave}
              disabled={loading}
            >
              {loading ? "Guardando..." : "Guardar cambios"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const [secrets, setSecrets] = useState([]);
  const [loadError, setLoadError] = useState("");
  const [site, setSite] = useState("");
  const [password, setPassword] = useState("");
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [editTarget, setEditTarget] = useState(null);

  const loadSecrets = useCallback(async () => {
    try {
      const data = await getSecrets();
      setSecrets(data);
      setLoadError("");
    } catch {
      setLoadError("No se pudieron cargar los datos de la bóveda.");
    }
  }, []);

  useEffect(() => {
    loadSecrets();
  }, [loadSecrets]);

  async function handleSave() {
    if (!site.trim() || !password.trim()) {
      setSaveError("El sitio y la contraseña son requeridos.");
      return;
    }
    try {
      await saveSecret(site, password);
      setSite("");
      setPassword("");
      setSaveError("");
      await loadSecrets();
    } catch {
      setSaveError("No se pudo guardar el secreto.");
    }
  }

  async function handleDelete(id) {
    if (!window.confirm("¿Eliminar este secreto?")) return;
    try {
      await deleteSecret(id);
      await loadSecrets();
    } catch {
      alert("No se pudo eliminar.");
    }
  }

  async function handleEditSave(id, newSite, newPassword) {
    try {
      await updateSecret(id, newSite, newPassword);
      setEditTarget(null);
      await loadSecrets();
    } catch {
      alert("No se pudo actualizar.");
    }
  }

  function logout() {
    localStorage.removeItem("token");
    navigate("/");
  }

  return (
    <div className="dashboard-bg">
      {editTarget && (
        <EditModal
          secret={editTarget}
          onClose={() => setEditTarget(null)}
          onSave={handleEditSave}
        />
      )}

      <nav className="navbar navbar-expand-lg navbar-dark bg-dark shadow-sm">
        <div className="container-fluid px-4">
          <a className="navbar-brand d-flex align-items-center gap-2" href="#">
            <i className="bi bi-shield-lock-fill fs-4"></i>
            SecureVault
          </a>
          <div className="ms-auto d-flex align-items-center gap-3">
            <span className="text-white-50 small">Bóveda personal</span>
            <button
              className="btn btn-outline-light btn-sm px-3"
              onClick={logout}
            >
              <i className="bi bi-box-arrow-right me-1"></i> Cerrar sesión
            </button>
          </div>
        </div>
      </nav>

      <main className="container py-5">
        <div className="row justify-content-center">
          <div className="col-lg-10 col-xl-8">
            {/* Save new secret */}
            <div className="card mb-5">
              <div className="card-body p-4 p-md-5">
                <h4 className="card-title mb-4 d-flex align-items-center gap-2">
                  <i className="bi bi-plus-circle-fill text-success"></i>
                  Guardar nueva contraseña
                </h4>
                <div className="row g-3">
                  <div className="col-md-5">
                    <label className="form-label fw-medium">
                      Sitio / Aplicación
                    </label>
                    <div className="input-group">
                      <span className="input-group-text">
                        <i className="bi bi-globe"></i>
                      </span>
                      <input
                        type="text"
                        className="form-control"
                        placeholder="ej. netflix.com, gmail.com"
                        value={site}
                        onChange={(e) => setSite(e.target.value)}
                        autoComplete="off"
                      />
                    </div>
                  </div>
                  <div className="col-md-5">
                    <label className="form-label fw-medium">Contraseña</label>
                    <div className="input-group">
                      <span className="input-group-text">
                        <i className="bi bi-key"></i>
                      </span>
                      <input
                        type={showNewPassword ? "text" : "password"}
                        className="form-control"
                        placeholder="••••••••••••"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        autoComplete="new-password"
                      />
                      <button
                        className="btn btn-outline-secondary"
                        type="button"
                        onClick={() => setShowNewPassword((v) => !v)}
                      >
                        <i
                          className={`bi ${showNewPassword ? "bi-eye-slash" : "bi-eye"}`}
                        ></i>
                      </button>
                    </div>
                  </div>
                  <div className="col-md-2 d-flex align-items-end">
                    <button
                      className="btn btn-success w-100"
                      onClick={handleSave}
                    >
                      <i className="bi bi-save me-1"></i> Guardar
                    </button>
                  </div>
                </div>
                {saveError && (
                  <div className="text-danger mt-3 small">{saveError}</div>
                )}
              </div>
            </div>

            {/* Secrets list */}
            <div className="card">
              <div className="card-header bg-white border-0 pt-4 pb-0 px-4 px-md-5">
                <h4 className="mb-0 d-flex align-items-center gap-2">
                  <i className="bi bi-safe2-fill text-primary"></i>
                  Mi Vault
                </h4>
              </div>
              <div className="card-body p-4 p-md-5">
                {loadError ? (
                  <p className="text-danger">{loadError}</p>
                ) : secrets.length === 0 ? (
                  <div className="text-center py-5">
                    <i
                      className="bi bi-safe text-muted"
                      style={{ fontSize: "4rem" }}
                    ></i>
                    <p className="mt-3 text-muted">
                      Tu bóveda está vacía.
                      <br />
                      Comienza guardando tu primera contraseña.
                    </p>
                  </div>
                ) : (
                  <div className="table-responsive">
                    <table className="table table-hover align-middle">
                      <thead>
                        <tr>
                          <th scope="col">Sitio / Servicio</th>
                          <th scope="col">Contraseña</th>
                          <th scope="col" className="text-end">
                            Acciones
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {secrets.map((s) => (
                          <tr key={s.id}>
                            <td>{s.site}</td>
                            <td>
                              <PasswordCell password={s.password} />
                            </td>
                            <td className="text-end">
                              <button
                                className="btn btn-sm btn-warning me-1 action-btn"
                                title="Editar"
                                onClick={() => setEditTarget(s)}
                              >
                                <i className="bi bi-pencil"></i>
                              </button>
                              <button
                                className="btn btn-sm btn-danger action-btn"
                                title="Eliminar"
                                onClick={() => handleDelete(s.id)}
                              >
                                <i className="bi bi-trash"></i>
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
