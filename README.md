# ✨ RePhraseAI — GenAI Text Rephrasing & Paraphrasing System

Input text → preprocessing → FLAN-T5 (Transformer) → post-processing → quality evaluation → explainable output.
A hybrid project: **LSTM / BiLSTM / GRU seq2seq models built from scratch** (to demonstrate sequence modelling) compared against a **fine-tuned FLAN-T5** (to demonstrate modern GenAI). Not an API wrapper: all models run locally.

## Folder structure & purpose
```
RePhraseAI/
├── frontend/                 React + Vite + Tailwind UI
│   └── src/ pages/ components/ context/ hooks/ services/ utils/
├── backend/                  FastAPI server
│   ├── main.py               `uvicorn main:app` shortcut
│   └── app/
│       ├── main.py           app factory, CORS, router registration
│       ├── config.py         env-based settings
│       ├── database.py       SQLAlchemy engine (SQLite default / PostgreSQL)
│       ├── models/           ORM tables: users, rephrase_history, revoked_tokens
│       ├── schemas/          Pydantic request/response models
│       ├── routes/           auth.py, rephrase.py, history.py
│       ├── services/
│       │   ├── preprocessing.py     clean, sentence split, chunking
│       │   ├── prompt_service.py    style-specific prompt templates
│       │   ├── rephrase_service.py  FLAN-T5 generation + post-processing + ranking
│       │   ├── evaluation_service.py cosine, BLEU, ROUGE, BERTScore, perplexity
│       │   └── analysis_service.py  diff/explainability, readability, tone, grammar
│       └── utils/            JWT + bcrypt, auth dependencies, device selection
├── training/
│   ├── preprocessing.py      dataset download/clean/split
│   ├── rnn_seq2seq.py        LSTM/GRU/BiLSTM encoder-decoder + attention (core code)
│   ├── train_lstm.py  train_gru.py   thin launchers
│   ├── train_transformer.py  FLAN-T5 fine-tuning (Hugging Face)
│   └── evaluate.py           model comparison + graphs
├── data/ raw/ processed/ train/ validation/ test/
├── models/                   trained weights (lstm, bilstm, gru, flan-t5-paraphrase)
├── notebooks/                data_analysis, model_training, evaluation
└── docs/                     architecture.md methodology.md api.md database_schema.md academic_report.md results/
```

## Setup (Windows commands in comments)
Prerequisites: Python 3.10+, Node 18+. (GPU optional.)

```bash
# 1. Python virtual environment
cd RePhraseAI
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r training/requirements.txt      # includes backend requirements
cd frontend && npm install && cd ..

# 3. Prepare the dataset (needs internet once; PAWS ≈ 50k paraphrase pairs)
cd training
python preprocessing.py --dataset paws --max-samples 30000    # drop --max-samples for full data
# Quora / ParaNMT-style CSV:  python preprocessing.py --dataset csv --csv quora.csv --src-col question1 --tgt-col question2 --label-col is_duplicate

# 4. Train models (CPU works with the small settings below; add --device cuda for GPU)
python train_lstm.py --epochs 10                    # LSTM
python train_lstm.py --epochs 10 --bidirectional    # BiLSTM
python train_gru.py  --epochs 10                    # GRU
python train_transformer.py --model google/flan-t5-small --epochs 3 --max-train 20000
python evaluate.py --samples 200 --include-zero-shot   # comparison table + graphs in docs/results/
cd ..

# 5. Database
cd backend
cp .env.example .env        # Windows: copy .env.example .env   (edit JWT_SECRET)
#   SQLite works out of the box (file backend/rephraseai.db, tables auto-created).
#   PostgreSQL:  createdb rephraseai ; set DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/rephraseai

# 6. Start the API  (first call downloads google/flan-t5-base unless you trained your own model)
uvicorn app.main:app --reload --port 8000           # or: uvicorn main:app --reload
# Swagger UI: http://localhost:8000/docs

# 7. Start the frontend (new terminal)
cd frontend && npm run dev                           # http://localhost:5173
```
To use the fine-tuned model, simply train it — the backend auto-loads `models/flan-t5-paraphrase`. To use a smaller base model: `MODEL_NAME=google/flan-t5-small` in `.env`.

## Test the APIs
```bash
curl http://localhost:8000/api/health
curl -X POST http://localhost:8000/api/auth/register -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"secret123"}'
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"secret123"}' | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
curl -X POST http://localhost:8000/api/rephrase -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"text":"Artificial intelligence is changing the world.","style":"professional","temperature":0.7}'
curl -X POST http://localhost:8000/api/evaluate -H "Content-Type: application/json" \
  -d '{"original_text":"Machine learning helps computers learn from data.","rephrased_text":"Machine learning enables computers to learn using data."}'
curl http://localhost:8000/api/history -H "Authorization: Bearer $TOKEN"
cd backend && pytest -q          # unit tests (no model download needed)
```

## Run the complete application (quick path, no training)
1. `pip install -r backend/requirements.txt` · `cd frontend && npm install`
2. Terminal A: `cd backend && uvicorn app.main:app --reload`
3. Terminal B: `cd frontend && npm run dev` → open http://localhost:5173 → Sign up → Rephraser.

## Notes
- Anonymous users can rephrase; history/dashboard require login. Logout revokes the JWT server-side.
- BERTScore uses `distilbert-base-uncased` (light). Set `ENABLE_BERTSCORE=false` to speed up responses.
- Full documentation: `docs/`. Academic write-up and viva Q&A: `docs/academic_report.md`.
