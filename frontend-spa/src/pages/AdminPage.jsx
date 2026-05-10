import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  getAdminAuditLogs,
  getActiveUsers,
  getUserSessions,
  getUsers,
  revokeUserSessions,
  updateUserRole,
  updateUserStatus,
} from "../api/users";
import { clearAuthSession, getStoredUser } from "../api/auth";
import "./AdminPage.css";

function readStoredUser() {
  return getStoredUser();
}

export default function AdminPage() {
  const navigate = useNavigate();
  const [users, setUsers] = useState([]);
  const [loadError, setLoadError] = useState("");
  const [auditError, setAuditError] = useState("");
  const [sessionsError, setSessionsError] = useState("");
  const [actionMessage, setActionMessage] = useState("");
  const [activeUsers, setActiveUsers] = useState([]);
  const [currentUser] = useState(() => readStoredUser());
  const [editingUserId, setEditingUserId] = useState(null);
  const [newRole, setNewRole] = useState("");
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [activeSessions, setActiveSessions] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);

  const loadUsers = useCallback(async () => {
    try {
      const data = await getUsers();
      setUsers(data);
      setLoadError("");
    } catch {
      setLoadError("No se pudieron cargar los usuarios.");
    }
  }, []);

  const loadAuditLogs = useCallback(async () => {
    try {
      const data = await getAdminAuditLogs();
      setAuditLogs(data);
      setAuditError("");
    } catch {
      setAuditError("No se pudo cargar la bitácora de auditoría.");
    }
  }, []);

  const loadActiveUsers = useCallback(async () => {
    try {
      const data = await getActiveUsers();
      setActiveUsers(data);
    } catch {
      setActiveUsers([]);
    }
  }, []);

  const loadUserSessions = useCallback(async (userId) => {
    if (!userId) {
      setActiveSessions([]);
      return;
    }

    try {
      const data = await getUserSessions(userId);
      setActiveSessions(data);
      setSessionsError("");
    } catch {
      setSessionsError("No se pudieron cargar las sesiones activas.");
    }
  }, []);

  useEffect(() => {
    loadUsers();
    loadAuditLogs();
    loadActiveUsers();
  }, [loadUsers, loadAuditLogs, loadActiveUsers]);

  useEffect(() => {
    if (!users.length) {
      setSelectedUserId(null);
      setActiveSessions([]);
      return;
    }

    if (!selectedUserId || !users.some((u) => u.id === selectedUserId)) {
      setSelectedUserId(users[0].id);
      return;
    }

    loadUserSessions(selectedUserId);
  }, [users, selectedUserId, loadUserSessions]);

  async function handleRoleChange(userId, role) {
    try {
      await updateUserRole(userId, role);
      await loadUsers();
      await loadAuditLogs();
      setActionMessage("Rol actualizado correctamente.");
      setEditingUserId(null);
    } catch {
      alert("No se pudo actualizar el rol del usuario.");
    }
  }

  async function handleToggleStatus(user) {
    const nextStatus = !user.is_active;
    const statusLabel = nextStatus ? "activar" : "desactivar";
    if (!window.confirm(`¿Deseas ${statusLabel} la cuenta de ${user.email}?`)) {
      return;
    }

    try {
      await updateUserStatus(user.id, nextStatus);
      await loadUsers();
      await loadAuditLogs();
      if (!nextStatus && selectedUserId === user.id) {
        await loadUserSessions(user.id);
      }
      setActionMessage(
        nextStatus
          ? "Usuario activado correctamente."
          : "Usuario desactivado y sesiones revocadas.",
      );
    } catch {
      alert("No se pudo actualizar el estado del usuario.");
    }
  }

  async function handleRevokeSessions() {
    if (!selectedUserId) return;
    const targetUser = users.find((item) => item.id === selectedUserId);
    if (!targetUser) return;

    if (!window.confirm(`¿Revocar todas las sesiones activas de ${targetUser.email}?`)) {
      return;
    }

    try {
      const result = await revokeUserSessions(selectedUserId);
      await loadUserSessions(selectedUserId);
      await loadAuditLogs();
      setActionMessage(`Sesiones revocadas: ${result.revoked || 0}`);
    } catch {
      alert("No se pudieron revocar las sesiones activas.");
    }
  }

  async function handleRevokeActiveUserSessions(user) {
    if (!window.confirm(`¿Revocar todas las ${user.active_session_count} sesiones de ${user.email}?`)) {
      return;
    }

    try {
      const result = await revokeUserSessions(user.id);
      await loadActiveUsers();
      await loadAuditLogs();
      setActionMessage(`${result.revoked || 0} sesión/es revocada/s.`);
    } catch {
      alert("No se pudieron revocar las sesiones.");
    }
  }

  function logout() {
    clearAuthSession();
    navigate("/");
  }

  return (
    <div className="admin-page">
      <header className="admin-topbar">
        <div className="admin-brand">
          <i className="bi bi-shield-lock-fill"></i>
          <div>
            <h1>SecureVault Pro</h1>
            <p>Panel de administración</p>
          </div>
        </div>

        <div className="admin-userbox">
          <div>
            <p className="admin-user-email">{currentUser?.email || "admin@local"}</p>
            <p className="admin-user-role">Rol: {currentUser?.role || "admin"}</p>
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

      <main className="admin-main">
        <section className="admin-stats">
          <article className="admin-stat-card">
            <i className="bi bi-people-fill"></i>
            <div>
              <small>Total usuarios</small>
              <strong>{users.length}</strong>
            </div>
          </article>
          <article className="admin-stat-card">
            <i className="bi bi-person-badge-fill"></i>
            <div>
              <small>Administradores</small>
              <strong>{users.filter((u) => u.role === "admin").length}</strong>
            </div>
          </article>
          <article className="admin-stat-card">
            <i className="bi bi-person-check-fill"></i>
            <div>
              <small>Usuarios regulares</small>
              <strong>{users.filter((u) => u.role === "user").length}</strong>
            </div>
          </article>
          <article className="admin-stat-card">
            <i className="bi bi-toggle-on"></i>
            <div>
              <small>Usuarios activos</small>
              <strong>{users.filter((u) => u.is_active).length}</strong>
            </div>
          </article>
          <article className="admin-stat-card">
            <i className="bi bi-person-check-fill"></i>
            <div>
              <small>Conectados ahora</small>
              <strong>{activeUsers.length}</strong>
            </div>
          </article>
        </section>

        {actionMessage && <div className="alert alert-success">{actionMessage}</div>}

        <div className="admin-grid">
          <section className="admin-card connected-users-card">
            <h2>
              <i className="bi bi-people-fill me-2"></i>
              Usuarios conectados en este momento
            </h2>

            {activeUsers.length === 0 ? (
              <p className="text-secondary mb-0">No hay usuarios conectados en este momento.</p>
            ) : (
              <div className="users-table-container">
                <table className="users-table">
                  <thead>
                    <tr>
                      <th>Usuario</th>
                      <th>Correo</th>
                      <th>Rol</th>
                      <th>Sesiones activas</th>
                      <th>Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activeUsers.map((user) => (
                      <tr key={user.id}>
                        <td className="user-id">{user.id}</td>
                        <td className="user-email">{user.email}</td>
                        <td className="user-role">
                          <span className={`role-badge role-${user.role}`}>
                            {user.role === "admin" ? "Administrador" : "Usuario"}
                          </span>
                        </td>
                        <td className="user-sessions-count">
                          <strong>{user.active_session_count}</strong>
                        </td>
                        <td className="user-actions">
                          <button
                            className="btn btn-sm btn-outline-danger"
                            onClick={() => handleRevokeActiveUserSessions(user)}
                          >
                            <i className="bi bi-x-circle me-1"></i>
                            Revocar
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="admin-card users-card">
            <h2>
              <i className="bi bi-people-fill me-2"></i>
              Usuarios registrados
            </h2>

            {loadError && <div className="alert alert-danger">{loadError}</div>}

            {users.length === 0 ? (
              <div className="empty-state">
                <i className="bi bi-inbox"></i>
                <p>No hay usuarios registrados</p>
              </div>
            ) : (
              <div className="users-table-container">
                <table className="users-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Correo electrónico</th>
                      <th>Estado</th>
                      <th>Rol actual</th>
                      <th>Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((user) => (
                      <tr key={user.id}>
                        <td className="user-id">{user.id}</td>
                        <td className="user-email">{user.email}</td>
                        <td className="user-status">
                          <span className={`status-badge ${user.is_active ? "status-active" : "status-inactive"}`}>
                            {user.is_active ? "Activo" : "Inactivo"}
                          </span>
                        </td>
                        <td className="user-role">
                          {editingUserId === user.id ? (
                            <select
                              className="role-select"
                              value={newRole}
                              onChange={(e) => {
                                const selectedRole = e.target.value;
                                setNewRole(selectedRole);
                                if (selectedRole && selectedRole !== user.role) {
                                  handleRoleChange(user.id, selectedRole);
                                }
                              }}
                              autoFocus
                            >
                              <option value="">Seleccionar rol...</option>
                              <option value="user">Usuario</option>
                              <option value="admin">Administrador</option>
                            </select>
                          ) : (
                            <span className={`role-badge role-${user.role}`}>
                              {user.role === "admin" ? "Administrador" : "Usuario"}
                            </span>
                          )}
                        </td>
                        <td className="user-actions">
                          {currentUser?.email !== user.email && (
                            <div className="table-actions">
                              <button
                                className="btn btn-sm btn-outline-primary"
                                onClick={() => {
                                  setEditingUserId(user.id);
                                  setNewRole(user.role);
                                }}
                                disabled={editingUserId === user.id}
                              >
                                <i className="bi bi-pencil-fill me-1"></i>
                                Cambiar rol
                              </button>
                              <button
                                className="btn btn-sm btn-outline-warning"
                                onClick={() => handleToggleStatus(user)}
                              >
                                <i className={`bi ${user.is_active ? "bi-person-dash" : "bi-person-check"} me-1`}></i>
                                {user.is_active ? "Desactivar" : "Activar"}
                              </button>
                            </div>
                          )}
                          {currentUser?.email === user.email && (
                            <span className="self-indicator">Eres tú</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="admin-card sessions-card">
            <h2>
              <i className="bi bi-phone me-2"></i>
              Sesiones activas
            </h2>

            <div className="sessions-toolbar">
              <select
                className="role-select"
                value={selectedUserId || ""}
                onChange={(e) => setSelectedUserId(Number(e.target.value) || null)}
              >
                {users.map((user) => (
                  <option key={user.id} value={user.id}>
                    {user.email}
                  </option>
                ))}
              </select>
              <button
                className="btn btn-sm btn-outline-danger"
                type="button"
                onClick={handleRevokeSessions}
                disabled={!selectedUserId}
              >
                Revocar sesiones
              </button>
            </div>

            {sessionsError && <div className="alert alert-danger">{sessionsError}</div>}

            {activeSessions.length === 0 ? (
              <p className="text-secondary mb-0">No hay sesiones activas para el usuario seleccionado.</p>
            ) : (
              <div className="users-table-container">
                <table className="users-table">
                  <thead>
                    <tr>
                      <th>ID sesión</th>
                      <th>Emitida</th>
                      <th>Expira</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activeSessions.map((session) => (
                      <tr key={session.id}>
                        <td className="user-id">{session.id}</td>
                        <td>{new Date(session.issued_at).toLocaleString()}</td>
                        <td>{new Date(session.expires_at).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="admin-card audit-card">
            <h2>
              <i className="bi bi-journal-check me-2"></i>
              Bitácora de auditoría
            </h2>

            {auditError && <div className="alert alert-danger">{auditError}</div>}

            {auditLogs.length === 0 ? (
              <p className="text-secondary mb-0">No hay eventos de auditoría registrados.</p>
            ) : (
              <div className="users-table-container">
                <table className="users-table">
                  <thead>
                    <tr>
                      <th>Fecha</th>
                      <th>Acción</th>
                      <th>Actor</th>
                      <th>Objetivo</th>
                      <th>Detalle</th>
                    </tr>
                  </thead>
                  <tbody>
                    {auditLogs.map((entry) => (
                      <tr key={entry.id}>
                        <td>{new Date(entry.created_at).toLocaleString()}</td>
                        <td>{entry.action}</td>
                        <td>{entry.actor_email}</td>
                        <td>{entry.target_email || "N/A"}</td>
                        <td>{entry.details || "-"}</td>
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
