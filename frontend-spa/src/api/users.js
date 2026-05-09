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
