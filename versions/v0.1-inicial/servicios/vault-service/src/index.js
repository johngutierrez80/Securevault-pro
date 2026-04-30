require("dotenv").config();
const express = require("express");
const cors = require("cors");
const helmet = require("helmet");
const rateLimit = require("express-rate-limit");
const jwt = require("jsonwebtoken");
const { pool, initDb } = require("./db");
const { encrypt, decrypt } = require("./crypto");

const app = express();
const port = Number(process.env.PORT || 3002);
const jwtSecret = process.env.JWT_SECRET || "super-secret-jwt-key-change-me";

function addOneMonth(baseDate) {
  const result = new Date(baseDate);
  result.setMonth(result.getMonth() + 1);
  return result;
}

function resolveExpiration(expiresAtInput) {
  const minExpiration = addOneMonth(new Date());
  if (!expiresAtInput) {
    return minExpiration;
  }

  const providedDate = new Date(expiresAtInput);
  if (Number.isNaN(providedDate.getTime())) {
    return null;
  }

  if (providedDate < minExpiration) {
    return minExpiration;
  }

  return providedDate;
}

app.use(helmet());
app.use(cors());
app.use(express.json());
app.use(
  rateLimit({
    windowMs: 60 * 1000,
    limit: 120,
    standardHeaders: true,
    legacyHeaders: false
  })
);

function requireAuth(req, res, next) {
  const authHeader = req.headers.authorization || "";
  const token = authHeader.startsWith("Bearer ") ? authHeader.slice(7) : null;
  if (!token) {
    return res.status(401).json({ error: "token requerido" });
  }

  try {
    req.user = jwt.verify(token, jwtSecret);
    return next();
  } catch (_error) {
    return res.status(401).json({ error: "token invalido" });
  }
}

app.get("/health", (_req, res) => {
  res.json({ status: "ok", service: "vault-service" });
});

app.post("/secrets", requireAuth, async (req, res) => {
  try {
    const { name, value, expiresAt } = req.body;
    if (!name || !value) {
      return res.status(400).json({ error: "name y value son obligatorios" });
    }

    const resolvedExpiration = resolveExpiration(expiresAt);
    if (!resolvedExpiration) {
      return res.status(400).json({ error: "expiresAt invalido" });
    }

    const encrypted = encrypt(value);
    const result = await pool.query(
      `INSERT INTO secrets (user_id, name, iv, ciphertext, auth_tag, expires_at)
       VALUES ($1, $2, $3, $4, $5, $6)
       RETURNING id, user_id, name, expires_at, created_at`,
      [
        req.user.sub,
        name,
        encrypted.iv,
        encrypted.ciphertext,
        encrypted.authTag,
        resolvedExpiration.toISOString()
      ]
    );

    return res.status(201).json(result.rows[0]);
  } catch (_error) {
    return res.status(500).json({ error: "error interno" });
  }
});

app.get("/secrets", requireAuth, async (req, res) => {
  try {
    const result = await pool.query(
      "SELECT id, user_id, name, iv, ciphertext, auth_tag, expires_at, created_at FROM secrets WHERE user_id = $1 ORDER BY id DESC",
      [req.user.sub]
    );

    const payload = result.rows.map((row) => ({
      id: row.id,
      name: row.name,
      value: decrypt({
        iv: row.iv,
        ciphertext: row.ciphertext,
        authTag: row.auth_tag
      }),
      expiresAt: row.expires_at ? new Date(row.expires_at).toISOString() : null,
      createdAt: row.created_at
    }));

    return res.json(payload);
  } catch (_error) {
    return res.status(500).json({ error: "error interno" });
  }
});

app.delete("/secrets/:id", requireAuth, async (req, res) => {
  try {
    const secretId = Number(req.params.id);
    if (Number.isNaN(secretId)) {
      return res.status(400).json({ error: "id invalido" });
    }

    const deleted = await pool.query(
      "DELETE FROM secrets WHERE id = $1 AND user_id = $2 RETURNING id",
      [secretId, req.user.sub]
    );

    if (!deleted.rowCount) {
      return res.status(404).json({ error: "secreto no encontrado" });
    }

    return res.status(204).send();
  } catch (_error) {
    return res.status(500).json({ error: "error interno" });
  }
});

(async () => {
  try {
    await initDb();
    app.listen(port, () => {
      console.log(`vault-service escuchando en puerto ${port}`);
    });
  } catch (error) {
    console.error("Error iniciando vault-service", error);
    process.exit(1);
  }
})();
