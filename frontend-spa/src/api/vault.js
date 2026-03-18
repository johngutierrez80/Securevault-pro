function authHeaders() {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${localStorage.getItem("token")}`,
  };
}

export async function getSecrets() {
  const res = await fetch("/vault/secret", { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to load secrets");
  return res.json();
}

export async function saveSecret(site, password) {
  const res = await fetch("/vault/secret", {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ site, password }),
  });
  if (!res.ok) throw new Error("Save failed");
}

export async function updateSecret(id, site, password) {
  const res = await fetch(`/vault/secret/${id}`, {
    method: "PUT",
    headers: authHeaders(),
    body: JSON.stringify({ site, password }),
  });
  if (!res.ok) throw new Error("Update failed");
}

export async function deleteSecret(id) {
  const res = await fetch(`/vault/secret/${id}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
  });
  if (!res.ok) throw new Error("Delete failed");
}
