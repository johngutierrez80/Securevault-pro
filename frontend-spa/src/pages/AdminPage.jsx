import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { getUsers, updateUserRole } from "../api/users";
import { clearAuthSession, getStoredUser } from "../api/auth";
import "./AdminPage.css";

function readStoredUser() {
  return getStoredUser();
}

export default function AdminPage() {
  const navigate = useNavigate();
  const [users, setUsers] = useState([]);
  const [loadError, setLoadError] = useState("");
  const [currentUser] = useState(() => readStoredUser());
  const [editingUserId, setEditingUserId] = useState(null);
  const [newRole, setNewRole] = useState("");

  const loadUsers = useCallback(async () => {
    try {
      const data = await getUsers();
      setUsers(data);
      setLoadError("");
    } catch {
      setLoadError("No se pudieron cargar los usuarios.");
    }
  }, []);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  async function handleRoleChange(userId, role) {
    try {
      await updateUserRole(userId, role);
      await loadUsers();
      setEditingUserId(null);
    } catch {
      alert("No se pudo actualizar el rol del usuario.");
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
        </section>

        <div className="admin-grid">
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
                      <th>Rol actual</th>
                      <th>Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((user) => (
                      <tr key={user.id}>
                        <td className="user-id">{user.id}</td>
                        <td className="user-email">{user.email}</td>
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
        </div>
      </main>
    </div>
  );
}
