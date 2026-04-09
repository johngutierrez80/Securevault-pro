// main.js - Frontend logic for SecureVault

function showMessage(text, isError = true) {
  const message = document.getElementById("message");
  if (!message) return;
  message.textContent = text;
  message.classList.toggle("text-danger", isError);
  message.classList.toggle("text-success", !isError);
}

function getAuthErrorMessage(response, data, action) {
  if (
    response.status === 400 ||
    response.status === 401 ||
    response.status === 422
  ) {
    return "Credenciales incorrectas";
  }

  if (typeof data?.detail === "string" && data.detail.trim()) {
    return "Credenciales incorrectas";
  }

  return "Credenciales incorrectas";
}

function getAuthInputs() {
  const username = document.getElementById("user").value.trim();
  const password = document.getElementById("pass").value.trim();

  if (!username || !password) {
    showMessage("Credenciales incorrectas", true);
    return null;
  }

  return { username, password };
}

async function login() {
  const credentials = getAuthInputs();
  if (!credentials) {
    return;
  }

  try {
    let response = await fetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(credentials),
    });
    let data = await response.json();

    if (response.ok) {
      localStorage.setItem("token", data.access_token);
      window.location = "dashboard.html";
    } else {
      showMessage(getAuthErrorMessage(response, data, "login"), true);
    }
  } catch {
    showMessage(
      "No fue posible conectar con el servicio de autenticacion.",
      true,
    );
  }
}

async function register() {
  const credentials = getAuthInputs();
  if (!credentials) {
    return;
  }

  try {
    let response = await fetch("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(credentials),
    });
    let data = await response.json();

    if (response.ok) {
      showMessage("Usuario creado. Ahora puedes iniciar sesion.", false);
    } else {
      showMessage(getAuthErrorMessage(response, data, "register"), true);
    }
  } catch {
    showMessage(
      "No fue posible conectar con el servicio de autenticacion.",
      true,
    );
  }
}

async function save() {
  let site = document.getElementById("site").value;
  let password = document.getElementById("password").value;
  let token = localStorage.getItem("token");

  let response = await fetch("/vault/secret", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ site: site, password: password }),
  });

  if (response.ok) {
    load();
  } else {
    alert("Save failed");
  }
}

async function editSecret(id) {
  const site = prompt("Nuevo sitio:");
  if (!site) return;
  const password = prompt("Nueva contraseña:");
  if (password === null) return;

  let token = localStorage.getItem("token");
  let response = await fetch(`/vault/secret/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ site, password }),
  });

  if (response.ok) {
    load();
  } else {
    alert("Update failed");
  }
}

async function deleteSecret(id) {
  if (!confirm("Eliminar este secreto?")) return;

  let token = localStorage.getItem("token");
  let response = await fetch(`/vault/secret/${id}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });

  if (response.ok) {
    load();
  } else {
    alert("Delete failed");
  }
}

function createPasswordCell(password) {
  const wrapper = document.createElement("div");
  wrapper.className = "input-group input-group-sm vault-pass-group";

  const prefix = document.createElement("span");
  prefix.className = "input-group-text";
  prefix.innerHTML = '<i class="bi bi-key"></i>';

  const input = document.createElement("input");
  input.className = "form-control password-cell";
  input.type = "password";
  input.value = password;
  input.readOnly = true;

  const toggle = document.createElement("button");
  toggle.className = "btn btn-outline-secondary";
  toggle.type = "button";
  toggle.setAttribute("title", "Mostrar u ocultar contraseña");
  toggle.innerHTML = '<i class="bi bi-eye"></i>';
  toggle.addEventListener("click", () => {
    const icon = toggle.querySelector("i");
    if (input.type === "password") {
      input.type = "text";
      icon.classList.replace("bi-eye", "bi-eye-slash");
    } else {
      input.type = "password";
      icon.classList.replace("bi-eye-slash", "bi-eye");
    }
  });

  wrapper.appendChild(prefix);
  wrapper.appendChild(input);
  wrapper.appendChild(toggle);
  return wrapper;
}

async function load() {
  let token = localStorage.getItem("token");
  let list = document.getElementById("list");
  let emptyState = document.getElementById("emptyState");

  if (!list) return;

  if (!token) {
    window.location = "index.html";
    return;
  }

  let response = await fetch("/vault/secret", {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok) {
    list.innerHTML =
      '<tr><td colspan="3" class="text-danger">No se pudieron cargar los datos de la bóveda.</td></tr>';
    if (emptyState) emptyState.classList.add("d-none");
    return;
  }

  let data = await response.json();
  list.innerHTML = "";

  if (!Array.isArray(data) || data.length === 0) {
    if (emptyState) emptyState.classList.remove("d-none");
    return;
  }

  if (emptyState) emptyState.classList.add("d-none");

  data.forEach((s) => {
    const tr = document.createElement("tr");

    const siteTd = document.createElement("td");
    siteTd.textContent = s.site;

    const passTd = document.createElement("td");
    passTd.appendChild(createPasswordCell(s.password));

    const actionsTd = document.createElement("td");
    actionsTd.className = "text-end";

    const editBtn = document.createElement("button");
    editBtn.className = "btn btn-sm btn-warning me-1 action-btn";
    editBtn.title = "Editar";
    editBtn.innerHTML = '<i class="bi bi-pencil"></i>';
    editBtn.addEventListener("click", () => editSecret(s.id));

    const deleteBtn = document.createElement("button");
    deleteBtn.className = "btn btn-sm btn-danger action-btn";
    deleteBtn.title = "Eliminar";
    deleteBtn.innerHTML = '<i class="bi bi-trash"></i>';
    deleteBtn.addEventListener("click", () => deleteSecret(s.id));

    actionsTd.appendChild(editBtn);
    actionsTd.appendChild(deleteBtn);

    tr.appendChild(siteTd);
    tr.appendChild(passTd);
    tr.appendChild(actionsTd);

    list.appendChild(tr);
  });
}

function logout() {
  localStorage.removeItem("token");
  window.location = "index.html";
}

// Load secrets on dashboard load
if (window.location.pathname.includes("dashboard.html")) {
  load();
}
