require("dotenv").config();
const express = require("express");
const cron = require("node-cron");
const { pool } = require("./db");

const app = express();
const port = Number(process.env.PORT || 3003);
const schedule = process.env.CLEANUP_CRON || "*/1 * * * *";

let lastRun = null;
let lastDeleted = 0;

async function cleanupExpiredSecrets() {
  const result = await pool.query(
    `DELETE FROM secrets
     WHERE expires_at IS NOT NULL
       AND GREATEST(expires_at, created_at + INTERVAL '1 month') <= NOW()
     RETURNING id`
  );
  lastRun = new Date().toISOString();
  lastDeleted = result.rowCount;
  console.log(`worker-service cleanup: ${lastDeleted} secretos eliminados`);
}

app.get("/health", (_req, res) => {
  res.json({
    status: "ok",
    service: "worker-service",
    schedule,
    lastRun,
    lastDeleted
  });
});

(async () => {
  try {
    await pool.query("SELECT 1");
    cron.schedule(schedule, async () => {
      try {
        await cleanupExpiredSecrets();
      } catch (error) {
        console.error("Error en tarea de limpieza", error);
      }
    });

    app.listen(port, () => {
      console.log(`worker-service escuchando en puerto ${port}`);
    });
  } catch (error) {
    console.error("Error iniciando worker-service", error);
    process.exit(1);
  }
})();
