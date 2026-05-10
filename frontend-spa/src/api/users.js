import { getAuthToken } from "./auth";

function authHeaders() {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${getAuthToken() || ""}`,
  };
}

export async function getUsers() {
  const res = await fetch("/auth/users", { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to load users");
  return res.json();
}

export async function updateUserRole(userId, newRole) {
  const res = await fetch(`/auth/users/${userId}/role`, {
    method: "PATCH",
    headers: authHeaders(),
    body: JSON.stringify({ role: newRole }),
  });
  if (!res.ok) throw new Error("Failed to update user role");
  return res.json();
}

export async function updateUserStatus(userId, isActive) {
  const res = await fetch(`/auth/users/${userId}/status`, {
    method: "PATCH",
    headers: authHeaders(),
    body: JSON.stringify({ is_active: isActive }),
  });
  if (!res.ok) throw new Error("Failed to update user status");
  return res.json();
}

export async function getUserSessions(userId) {
  const res = await fetch(`/auth/users/${userId}/sessions`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to load user sessions");
  return res.json();
}

export async function revokeUserSessions(userId) {
  const res = await fetch(`/auth/users/${userId}/sessions/revoke`, {
    method: "POST",
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error("Failed to revoke user sessions");
  return res.json();
}

export async function getAdminAuditLogs() {
  const res = await fetch("/auth/admin/audit-logs", { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to load admin audit logs");
  return res.json();
}

export async function getActiveUsers() {
  const res = await fetch("/auth/admin/active-users", { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to load active users");
  return res.json();
}
