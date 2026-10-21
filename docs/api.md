# REST API (base `http://localhost:8000`, interactive docs at `/docs`)

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | /api/auth/register | – | create account, returns JWT |
| POST | /api/auth/login | – | returns JWT + user |
| POST | /api/auth/logout | Bearer | revokes the token (blacklist) |
| GET | /api/auth/me | Bearer | current user |
| POST | /api/rephrase | optional | full pipeline; stores history if logged in |
| POST | /api/evaluate | – | metrics + explanation for any text pair |
| POST | /api/grammar | – | rule-based grammar correction |
| GET | /api/styles | – | available styles |
| GET | /api/models/comparison | – | LSTM/GRU/Transformer results (from evaluate.py) |
| GET | /api/history | Bearer | list (`favorites_only`, `search`, `limit`, `skip`) |
| GET | /api/history/stats/summary | Bearer | dashboard stats |
| PATCH | /api/history/{id}/favorite | Bearer | toggle favourite |
| DELETE | /api/history/{id} | Bearer | delete item |

## POST /api/rephrase
Request
```json
{"text":"Artificial intelligence is changing the world.","style":"professional","temperature":0.7,"num_results":1,"evaluate":true}
```
`style` ∈ standard, professional, simple, academic, creative, formal, casual, concise, expand · `temperature` 0–1.5 (0 = beam search) · `num_results` 1–3.

Response (abridged)
```json
{
  "original_text":"Artificial intelligence is changing the world.",
  "rephrased_text":"Artificial intelligence is transforming the modern world.",
  "style":"professional","model":"FLAN-T5 (fine-tuned)","temperature":0.7,
  "similarity_score":0.91,
  "candidates":[{"text":"...","similarity":0.91,"is_best":true,"diff":{"original_tokens":[{"t":"changing","type":"removed"}],"rephrased_tokens":[{"t":"transforming","type":"added"}]}}],
  "metrics":{"semantic_similarity":0.91,"bertscore_f1":0.93,"bleu":0.41,"rouge1":0.7,"rouge2":0.4,"rougeL":0.66,"lexical_change":0.3,"perplexity":38.2,"verdict":"Excellent paraphrase ..."},
  "explanation":{"replaced":[{"type":"replace","from":"changing","to":"transforming"}],"structure":{"structure_changed":false,"notes":["..."]},"meaning_preserved":true,"similarity_percent":91.0,"summary":"..."},
  "stats":{"original":{"words":6,"readability":{"flesch_reading_ease":0},"tone":{"label":"neutral"}},"rephrased":{}},
  "timings_ms":{"preprocess":0.2,"generation":850,"ranking":20,"evaluation":300},
  "history_id":12
}
```
(Numbers above are illustrative of the format, not measured results.)
Errors: 401 auth, 409 duplicate email, 422 validation (e.g. fewer than 3 words).
