async function parseJsonResponse(response) {
  const data = await response.json();
  return { ok: response.ok, status: response.status, data };
}

function readStorageValue(key) {
  return localStorage.getItem(key) || sessionStorage.getItem(key);
}

export function getAuthToken() {
  return readStorageValue("token");
}

export function getStoredUser() {
  const raw = readStorageValue("user");
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function storeUserProfile(user, remember = true) {
  localStorage.removeItem("user");
  sessionStorage.removeItem("user");
  if (!user) return;

  const target = remember ? localStorage : sessionStorage;
  target.setItem("user", JSON.stringify(user));
}

export function persistAuthSession(token, user, remember = true) {
  localStorage.removeItem("token");
  sessionStorage.removeItem("token");
  if (token) {
    const target = remember ? localStorage : sessionStorage;
    target.setItem("token", token);
  }
  storeUserProfile(user, remember);
}

export function clearAuthSession() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
  sessionStorage.removeItem("token");
  sessionStorage.removeItem("user");
}

export async function loginUser(email, password) {
  const response = await fetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return parseJsonResponse(response);
}

export async function registerUser(email, password) {
  const response = await fetch("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return parseJsonResponse(response);
}

export async function requestPasswordReset(email) {
  const response = await fetch("/auth/password-reset/request", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  return parseJsonResponse(response);
}

export async function resetPassword(email, resetToken, newPassword) {
  const response = await fetch("/auth/password-reset/confirm", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email,
      reset_token: resetToken,
      new_password: newPassword,
    }),
  });
  return parseJsonResponse(response);
}

export async function getCurrentUser() {
  const response = await fetch("/auth/me", {
    headers: { Authorization: `Bearer ${getAuthToken() || ""}` },
  });
  return parseJsonResponse(response);
}

export async function confirmEmail(email, verificationToken) {
  const response = await fetch("/auth/confirm-email", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email,
      verification_token: verificationToken,
    }),
  });
  return parseJsonResponse(response);
}

export async function resendVerificationEmail(email) {
  const response = await fetch("/auth/resend-verification-email", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  return parseJsonResponse(response);
}

export async function deleteUser(userId) {
  const response = await fetch(`/auth/users/${userId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${getAuthToken() || ""}` },
  });
  return parseJsonResponse(response);
}
