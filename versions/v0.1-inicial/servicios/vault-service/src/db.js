const { Pool } = require("pg");

const pool = new Pool({
  connectionString: process.env.DATABASE_URL
});

async function initDb() {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS secrets (
      id SERIAL PRIMARY KEY,
      user_id INTEGER NOT NULL,
      name TEXT NOT NULL,
      iv TEXT NOT NULL,
      ciphertext TEXT NOT NULL,
      auth_tag TEXT NOT NULL,
      expires_at TIMESTAMPTZ NULL,
      created_at TIMESTAMP NOT NULL DEFAULT NOW()
    )
  `);

  await pool.query(`
    DO $$
    BEGIN
      IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'secrets'
          AND column_name = 'expires_at'
          AND data_type = 'timestamp without time zone'
      ) THEN
        ALTER TABLE secrets
        ALTER COLUMN expires_at TYPE TIMESTAMPTZ
        USING expires_at AT TIME ZONE 'UTC';
      END IF;
    END
    $$;
  `);
}

module.exports = {
  pool,
  initDb
};
