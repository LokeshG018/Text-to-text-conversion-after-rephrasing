# Database schema (SQLAlchemy; SQLite by default, PostgreSQL via `DATABASE_URL`)
Tables are created automatically at startup (`Base.metadata.create_all`). Equivalent PostgreSQL DDL:

```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  hashed_password VARCHAR(255) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE rephrase_history (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  original_text TEXT NOT NULL,
  rephrased_text TEXT NOT NULL,
  style VARCHAR(30) NOT NULL,
  model VARCHAR(80) NOT NULL,
  temperature DOUBLE PRECISION,
  similarity_score DOUBLE PRECISION,
  metrics JSON,        -- bleu, rouge, bertscore, perplexity ...
  explanation JSON,    -- replaced words, structure notes
  is_favorite BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX ON rephrase_history (user_id, created_at DESC);
CREATE TABLE revoked_tokens (jti VARCHAR(64) PRIMARY KEY, expires_at TIMESTAMPTZ);
```
Example record: `{user_id, original_text, rephrased_text, style:"academic", model:"FLAN-T5 (fine-tuned)", similarity_score:0.91, created_at}`.
