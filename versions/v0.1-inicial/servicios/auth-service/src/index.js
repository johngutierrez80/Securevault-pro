require("dotenv").config();
const express = require("express");
const cors = require("cors");
const helmet = require("helmet");
const rateLimit = require("express-rate-limit");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const { pool, initDb } = require("./db");

const app = express();
const port = Number(process.env.PORT || 3001);
const jwtSecret = process.env.JWT_SECRET || "super-secret-jwt-key-change-me";

app.use(helmet());
app.use(cors());
app.use(express.json());
app.use(
  rateLimit({
    windowMs: 60 * 1000,
    limit: 60,
    standardHeaders: true,
    legacyHeaders: false
  })
);

app.get("/health", (_req, res) => {
  res.json({ status: "ok", service: "auth-service" });
});

app.post("/auth/register", async (req, res) => {
  try {
    const { email, password, role } = req.body;
    if (!email || !password) {
      return res.status(400).json({ error: "email y password son obligatorios" });
    }

    if (password.length < 8) {
      return res.status(400).json({ error: "password debe tener al menos 8 caracteres" });
    }

    const safeRole = role === "admin" ? "admin" : "user";
    const passwordHash = await bcrypt.hash(password, 10);

    const result = await pool.query(
      "INSERT INTO users (email, password_hash, role) VALUES ($1, $2, $3) RETURNING id, email, role, created_at",
      [email.toLowerCase(), passwordHash, safeRole]
    );

    return res.status(201).json(result.rows[0]);
  } catch (error) {
    if (error.code === "23505") {
      return res.status(409).json({ error: "usuario ya existe" });
    }
    return res.status(500).json({ error: "error interno" });
  }
});

app.post("/auth/login", async (req, res) => {
  try {
    const { email, password } = req.body;
    if (!email || !password) {
      return res.status(400).json({ error: "email y password son obligatorios" });
    }

    const result = await pool.query(
      "SELECT id, email, password_hash, role FROM users WHERE email = $1",
      [email.toLowerCase()]
    );

    if (!result.rowCount) {
      return res.status(401).json({ error: "credenciales invalidas" });
    }

    const user = result.rows[0];
    const valid = await bcrypt.compare(password, user.password_hash);
    if (!valid) {
      return res.status(401).json({ error: "credenciales invalidas" });
    }

    const token = jwt.sign(
      { sub: user.id, email: user.email, role: user.role },
      jwtSecret,
      { expiresIn: "2h" }
    );

    return res.json({
      accessToken: token,
      user: { id: user.id, email: user.email, role: user.role }
    });
  } catch (_error) {
    return res.status(500).json({ error: "error interno" });
  }
});

(async () => {
  try {
    await initDb();
    app.listen(port, () => {
      console.log(`auth-service escuchando en puerto ${port}`);
    });
  } catch (error) {
    console.error("Error iniciando auth-service", error);
    process.exit(1);
  }
})();
