# System architecture

```
React Frontend (Vite, Tailwind, Router, Context)
        ↓  axios (/api, JWT in Authorization header)
FastAPI REST API (routes: auth, rephrase, history)
        ↓
Authentication Layer (bcrypt password hash, JWT with jti, revocation list)
        ↓
Text Preprocessing (Unicode NFKC, whitespace/punctuation fix, sentence split, chunking ≤80 words)
        ↓
GenAI Rephrasing Service (prompt_service builds a style-specific instruction)
        ↓
Transformer Model (FLAN-T5 encoder-decoder; beam search if temperature=0 else nucleus sampling)
        ↓
Post-processing (strip prompt echoes, grammar_fix, punctuation) + candidate ranking
        ↓
Evaluation Service (cosine, BERTScore, BLEU, ROUGE, perplexity) + Analysis Service (diff, readability, tone)
        ↓
Database (users, rephrase_history)
        ↓
Response to Frontend (text, candidates, metrics, explanation, stats)
```

| Component | Responsibility |
|---|---|
| Frontend pages | Home, Rephraser, History, About/Model, Login/Register, Dashboard |
| `routes/*` | HTTP layer only; thin |
| `preprocessing.py` | normalise input, chunk long text so it fits the model window |
| `prompt_service.py` | prompt engineering: 9 style templates |
| `rephrase_service.py` | lazy-loaded model (fine-tuned folder if present, else `MODEL_NAME`), generation, ranking by `0.7·similarity + 0.3·wording change` |
| `evaluation_service.py` | all quantitative metrics; lazily loads embedding model, DistilBERT (BERTScore), DistilGPT-2 (perplexity) |
| `analysis_service.py` | explainability: token diff via `difflib`, structure notes, Flesch readability, lexicon tone detector, rule-based grammar correction |
| `auth` utilities | `bcrypt` hashing, HS256 JWT, blacklist on logout |

Design decisions: sync endpoints (FastAPI runs them in a threadpool, suitable for blocking PyTorch calls); SQLAlchemy so SQLite→PostgreSQL is only a URL change; models are lazy-loaded to keep startup fast.
