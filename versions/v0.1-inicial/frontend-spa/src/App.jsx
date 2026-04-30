import { useEffect, useMemo, useState } from "react";
import axios from "axios";

const authApiUrl = import.meta.env.VITE_AUTH_API_URL || "http://localhost:3001";
const vaultApiUrl = import.meta.env.VITE_VAULT_API_URL || "http://localhost:3002";

function getDefaultExpirationInput() {
  const date = new Date();
  date.setMonth(date.getMonth() + 1);
  date.setSeconds(0, 0);

  // Convierte a formato local YYYY-MM-DDTHH:mm para datetime-local.
  const timezoneOffsetMs = date.getTimezoneOffset() * 60000;
  return new Date(date.getTime() - timezoneOffsetMs).toISOString().slice(0, 16);
}

function App() {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState("");
  const [user, setUser] = useState(null);
  const [name, setName] = useState("");
  const [value, setValue] = useState("");
  const [expiresAt, setExpiresAt] = useState(getDefaultExpirationInput());
  const [secrets, setSecrets] = useState([]);
  const [message, setMessage] = useState("Bienvenido a SecureVault Pro MVP");

  const authHeaders = useMemo(() => ({
    headers: { Authorization: `Bearer ${token}` }
  }), [token]);

  async function registerOrLogin(event) {
    event.preventDefault();
    try {
      if (mode === "register") {
        await axios.post(`${authApiUrl}/auth/register`, { email, password });
        setMessage("Registro exitoso. Ahora inicia sesion.");
        setMode("login");
        return;
      }

      const response = await axios.post(`${authApiUrl}/auth/login`, { email, password });
      setToken(response.data.accessToken);
      setUser(response.data.user);
      setMessage(`Sesion iniciada como ${response.data.user.email}`);
    } catch (error) {
      setMessage(error.response?.data?.error || "Error en autenticacion");
    }
  }

  async function loadSecrets() {
    if (!token) {
      return;
    }

    try {
      const response = await axios.get(`${vaultApiUrl}/secrets`, authHeaders);
      setSecrets(response.data);
    } catch (error) {
      setMessage(error.response?.data?.error || "No se pudieron cargar secretos");
    }
  }

  async function createSecret(event) {
    event.preventDefault();
    try {
      await axios.post(
        `${vaultApiUrl}/secrets`,
        {
          name,
          value,
          expiresAt: expiresAt ? new Date(expiresAt).toISOString() : null
        },
        authHeaders
      );
      setName("");
      setValue("");
      setExpiresAt(getDefaultExpirationInput());
      setMessage("Secreto almacenado correctamente");
      await loadSecrets();
    } catch (error) {
      setMessage(error.response?.data?.error || "No se pudo crear el secreto");
    }
  }

  async function deleteSecret(id) {
    try {
      await axios.delete(`${vaultApiUrl}/secrets/${id}`, authHeaders);
      setMessage("Secreto eliminado");
      await loadSecrets();
    } catch (error) {
      setMessage(error.response?.data?.error || "No se pudo eliminar");
    }
  }

  function logout() {
    setToken("");
    setUser(null);
    setSecrets([]);
    setMessage("Sesion cerrada");
  }

  useEffect(() => {
    loadSecrets();
  }, [token]);

  return (
    <main className="layout">
      <section className="panel auth">
        <h1>SecureVault Pro</h1>
        <p>MVP de Avance 1</p>

        {!token && (
          <form onSubmit={registerOrLogin}>
            <div className="switch">
              <button type="button" onClick={() => setMode("login")} className={mode === "login" ? "active" : ""}>Login</button>
              <button type="button" onClick={() => setMode("register")} className={mode === "register" ? "active" : ""}>Registro</button>
            </div>
            <input
              type="email"
              placeholder="correo@dominio.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <input
              type="password"
              placeholder="Contrasena"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              minLength={8}
              required
            />
            <button type="submit">{mode === "login" ? "Entrar" : "Crear cuenta"}</button>
          </form>
        )}

        {token && (
          <div className="session">
            <p>Usuario: {user?.email}</p>
            <p>Rol: {user?.role}</p>
            <button onClick={logout}>Cerrar sesion</button>
          </div>
        )}

        <small>{message}</small>
      </section>

      <section className="panel dashboard">
        <h2>Dashboard de Secretos</h2>
        {!token && <p>Inicia sesion para administrar secretos.</p>}

        {token && (
          <>
            <form onSubmit={createSecret} className="secret-form">
              <input
                type="text"
                placeholder="Nombre del secreto"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
              <textarea
                placeholder="Valor del secreto"
                value={value}
                onChange={(e) => setValue(e.target.value)}
                required
              />
              <input
                type="datetime-local"
                value={expiresAt}
                onChange={(e) => setExpiresAt(e.target.value)}
              />
              <button type="submit">Guardar secreto</button>
              <button type="button" onClick={loadSecrets}>Refrescar</button>
            </form>

            <div className="secret-list">
              {secrets.length === 0 && <p>Aun no tienes secretos.</p>}
              {secrets.map((secret) => (
                <article key={secret.id}>
                  <h3>{secret.name}</h3>
                  <p>{secret.value}</p>
                  <small>Expira: {secret.expiresAt ? new Date(secret.expiresAt).toLocaleString() : "sin fecha"}</small>
                  <button onClick={() => deleteSecret(secret.id)}>Eliminar</button>
                </article>
              ))}
            </div>
          </>
        )}
      </section>
    </main>
  );
}

export default App;
