import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  getSecrets,
  saveSecret,
  updateSecret,
  deleteSecret,
  shareSecret,
} from "../api/vault";
import { clearAuthSession, getStoredUser } from "../api/auth";
import "./DashboardPage.css";

const CATEGORY_OPTIONS = ["password", "api_key", "token", "certificate", "other"];

function readStoredUser() {
  return getStoredUser();
}

function SecretCell({ value, category }) {
  const [visible, setVisible] = useState(false);
  const isMasked =
    category === "password" || category === "api_key" || category === "token";

  return (
    <div className="secret-cell">
      <input
        className="form-control secret-input"
        type={visible && isMasked ? "text" : isMasked ? "password" : "text"}
        value={value}
        readOnly
        onChange={() => {}}
      />
      {isMasked && (
        <button
          className="btn-show-secret"
          type="button"
          title="Mostrar u ocultar"
          onClick={() => setVisible((v) => !v)}
        >
          <i className={`bi ${visible ? "bi-eye-slash" : "bi-eye"}`}></i>
        </button>
      )}
    </div>
  );
}

function EditModal({ secret, onClose, onSave }) {
  const [name, setName] = useState(secret.site || "");
  const [category, setCategory] = useState(secret.category || "other");
  const [value, setValue] = useState(secret.password || "");
  const [description, setDescription] = useState(secret.description || "");
  const [loading, setLoading] = useState(false);

  async function handleSave() {
    if (!name.trim() || !value.trim()) return;
    setLoading(true);
    await onSave(secret.id, name, value, category, description);
    setLoading(false);
  }

  return (
    <div className="edit-backdrop" onClick={onClose}>
      <div className="edit-dialog" onClick={(e) => e.stopPropagation()}>
        <div className="edit-modal-card">
          <h5 className="edit-modal-title">Editar secreto</h5>
          
          <div className="edit-form-group">
            <label className="form-label">Nombre</label>
            <input
              className="form-control"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoFocus
            />
          </div>

          <div className="edit-form-group">
            <label className="form-label">Categoría</label>
            <select
              className="form-control"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              {CATEGORY_OPTIONS.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
          </div>

          <div className="edit-form-group">
            <label className="form-label">Valor del secreto</label>
            <input
              className="form-control"
              type="password"
              value={value}
              onChange={(e) => setValue(e.target.value)}
            />
          </div>

          <div className="edit-form-group">
            <label className="form-label">Descripción (opcional)</label>
            <textarea
              className="form-control"
              rows="2"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div className="edit-modal-actions">
            <button className="btn btn-secondary" onClick={onClose}>
              Cancelar
            </button>
            <button
              className="btn btn-primary"
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

function ShareModal({ secret, onClose }) {
  const [toEmail, setToEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null); // { ok: bool, msg: str }

  async function handleSend() {
    const email = toEmail.trim();
    if (!email) return;
    setLoading(true);
    setResult(null);
    try {
      const data = await shareSecret(secret.id, email);
      setResult({ ok: true, msg: data.msg || "Secreto enviado correctamente." });
    } catch (e) {
      setResult({ ok: false, msg: e.message || "No se pudo enviar el secreto." });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="edit-backdrop" onClick={onClose}>
      <div className="edit-dialog" onClick={(e) => e.stopPropagation()}>
        <div className="edit-modal-card">
          <h5 className="edit-modal-title">
            <i className="bi bi-envelope-fill me-2"></i>Compartir secreto por correo
          </h5>

          <p style={{ color: "#555", fontSize: "14px", marginBottom: "16px" }}>
            Se enviará el valor de <strong>{secret.site}</strong> al destinatario.
            La dirección de correo debe ser de confianza.
          </p>

          {!result && (
            <div className="edit-form-group">
              <label className="form-label">Correo del destinatario</label>
              <input
                className="form-control"
                type="email"
                placeholder="destinatario@dominio.com"
                value={toEmail}
                onChange={(e) => setToEmail(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
                autoFocus
                disabled={loading}
              />
            </div>
          )}

          {result && (
            <div className={`alert ${result.ok ? "alert-success" : "alert-danger"}`} style={{ marginTop: "12px" }}>
              {result.msg}
            </div>
          )}

          <div className="edit-modal-actions" style={{ marginTop: "20px" }}>
            <button className="btn btn-secondary" onClick={onClose}>
              {result?.ok ? "Cerrar" : "Cancelar"}
            </button>
            {!result?.ok && (
              <button
                className="btn btn-primary"
                onClick={handleSend}
                disabled={loading || !toEmail.trim()}
              >
                {loading ? (
                  <><i className="bi bi-hourglass-split me-1"></i>Enviando...</>
                ) : (
                  <><i className="bi bi-send-fill me-1"></i>Enviar</>
                )}
              </button>
            )}
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
  const [name, setName] = useState("");
  const [category, setCategory] = useState("other");
  const [value, setValue] = useState("");
  const [description, setDescription] = useState("");
  const [showNewValue, setShowNewValue] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [editTarget, setEditTarget] = useState(null);
  const [shareTarget, setShareTarget] = useState(null);
  const [currentUser] = useState(() => readStoredUser());

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
    if (!name.trim() || !value.trim()) {
      setSaveError("El nombre y el valor del secreto son requeridos.");
      return;
    }
    try {
      await saveSecret(name, value, category, description);
      setName("");
      setValue("");
      setCategory("other");
      setDescription("");
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

  async function handleEditSave(id, newName, newValue, newCategory, newDescription) {
    try {
      await updateSecret(id, newName, newValue, newCategory, newDescription);
      setEditTarget(null);
      await loadSecrets();
    } catch {
      alert("No se pudo actualizar.");
    }
  }

  function logout() {
    clearAuthSession();
    navigate("/");
  }

  return (
    <div className="vault-page">
      {editTarget && (
        <EditModal
          secret={editTarget}
          onClose={() => setEditTarget(null)}
          onSave={handleEditSave}
        />
      )}
      {shareTarget && (
        <ShareModal
          secret={shareTarget}
          onClose={() => setShareTarget(null)}
        />
      )}

      <header className="vault-topbar">
        <div className="vault-brand">
          <i className="bi bi-shield-lock-fill"></i>
          <div>
            <h1>SecureVault Pro</h1>
            <p>Panel de gestión de secretos cifrados</p>
          </div>
        </div>

        <div className="vault-userbox">
          <div>
            <p className="vault-user-email">{currentUser?.email || "usuario@local"}</p>
            <p className="vault-user-role">Rol: {currentUser?.role || "user"}</p>
          </div>
          <button
            className="btn btn-outline-light btn-sm"
            onClick={logout}
          >
            <i className="bi bi-box-arrow-right me-1"></i>
            Cerrar sesión
          </button>
        </div>
      </header>

      <main className="vault-main">
        <section className="vault-stats">
          <article className="stat-card">
            <i className="bi bi-safe2-fill"></i>
            <div>
              <small>Total secretos</small>
              <strong>{secrets.length}</strong>
            </div>
          </article>
          <article className="stat-card">
            <i className="bi bi-key-fill"></i>
            <div>
              <small>Datos sensibles</small>
              <strong>
                {
                  secrets.filter((s) =>
                    ["password", "api_key", "token"].includes(s.category || "other"),
                  ).length
                }
              </strong>
            </div>
          </article>
          <article className="stat-card">
            <i className="bi bi-person-badge-fill"></i>
            <div>
              <small>Cuenta activa</small>
              <strong>{currentUser?.role || "user"}</strong>
            </div>
          </article>
        </section>

        <div className="vault-grid">
          <section className="vault-card composer-card">
            <h2>
              <i className="bi bi-plus-circle-fill me-2"></i>
              Crear secreto
            </h2>

            <div className="form-grid">
              <div className="form-group">
                <label>Nombre</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="ej. AWS Producción"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  autoComplete="off"
                />
              </div>

              <div className="form-group">
                <label>Categoría</label>
                <select
                  className="form-control"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                >
                  {CATEGORY_OPTIONS.map((opt) => (
                    <option key={opt} value={opt}>
                      {opt}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-group">
              <label>Valor del secreto</label>
              <div className="secret-input-wrapper">
                <input
                  type={showNewValue ? "text" : "password"}
                  className="form-control"
                  placeholder="••••••••••••"
                  value={value}
                  onChange={(e) => setValue(e.target.value)}
                  autoComplete="off"
                />
                <button
                  className="btn-show"
                  type="button"
                  onClick={() => setShowNewValue((v) => !v)}
                  title="Mostrar/Ocultar"
                >
                  <i className={`bi ${showNewValue ? "bi-eye-slash" : "bi-eye"}`}></i>
                </button>
              </div>
            </div>

            <div className="form-group">
              <label>Descripción (opcional)</label>
              <textarea
                className="form-control"
                placeholder="Notas internas del secreto"
                rows="2"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>

            {saveError && <div className="alert alert-danger">{saveError}</div>}

            <button className="btn btn-primary btn-save" onClick={handleSave}>
              <i className="bi bi-floppy-fill me-1"></i>
              Guardar secreto
            </button>
          </section>

          <section className="vault-card list-card">
            <h2>
              <i className="bi bi-lock-fill me-2"></i>
              Secretos registrados ({secrets.length})
            </h2>

            {loadError && <div className="alert alert-danger">{loadError}</div>}

            {secrets.length === 0 ? (
              <div className="empty-state">
                <i className="bi bi-safe2"></i>
                <p>Tu bóveda está vacía</p>
                <small>Guarda el primer secreto usando el formulario.</small>
              </div>
            ) : (
              <div className="secrets-table-wrapper">
                <table className="secrets-table">
                  <thead>
                    <tr>
                      <th>Nombre</th>
                      <th>Categoría</th>
                      <th>Valor</th>
                      <th>Descripción</th>
                      <th className="text-end">Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {secrets.map((s) => (
                      <tr key={s.id}>
                        <td className="font-weight-bold">{s.site}</td>
                        <td>
                          <span className={`badge badge-${s.category || "other"}`}>
                            {s.category || "other"}
                          </span>
                        </td>
                        <td>
                          <SecretCell value={s.password} category={s.category} />
                        </td>
                        <td className="text-muted small">
                          {s.description
                            ? s.description.substring(0, 50) +
                              (s.description.length > 50 ? "..." : "")
                            : "-"}
                        </td>
                        <td className="text-end">
                          <button
                            className="btn btn-sm btn-primary me-2"
                            title="Editar"
                            onClick={() => setEditTarget(s)}
                          >
                            <i className="bi bi-pencil"></i>
                          </button>
                          <button
                            className="btn btn-sm btn-info me-2"
                            title="Compartir por correo"
                            onClick={() => setShareTarget(s)}
                          >
                            <i className="bi bi-envelope-fill"></i>
                          </button>
                          <button
                            className="btn btn-sm btn-danger"
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
          </section>
        </div>
      </main>
    </div>
  );
}
