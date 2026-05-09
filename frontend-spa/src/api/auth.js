async function parseJsonResponse(response) {
  const data = await response.json();
  return { ok: response.ok, status: response.status, data };
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
    headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
  });
  return parseJsonResponse(response);
}
