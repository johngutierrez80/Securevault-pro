import { getAuthToken } from "./auth";

function authHeaders() {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${getAuthToken() || ""}`,
  };
}

// Error especial para sesión expirada o revocada
export class SessionExpiredError extends Error {
  constructor() {
    super("Sesión expirada o revocada");
    this.isSessionExpired = true;
  }
}

// Wrapper central: lanza SessionExpiredError en 401/403
async function adminFetch(url, options = {}) {
  const res = await fetch(url, { headers: authHeaders(), ...options });
  if (res.status === 401 || res.status === 403) throw new SessionExpiredError();
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

export async function getUsers() {
  return adminFetch("/auth/users");
}

export async function updateUserRole(userId, newRole) {
  return adminFetch(`/auth/users/${userId}/role`, {
    method: "PATCH",
    body: JSON.stringify({ role: newRole }),
  });
}

export async function updateUserStatus(userId, isActive) {
  return adminFetch(`/auth/users/${userId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ is_active: isActive }),
  });
}

export async function getUserSessions(userId) {
  return adminFetch(`/auth/users/${userId}/sessions`);
}

export async function revokeUserSessions(userId) {
  return adminFetch(`/auth/users/${userId}/sessions/revoke`, { method: "POST" });
}

export async function getAdminAuditLogs() {
  return adminFetch("/auth/admin/audit-logs");
}

export async function getActiveUsers() {
  return adminFetch("/auth/admin/active-users");
}
