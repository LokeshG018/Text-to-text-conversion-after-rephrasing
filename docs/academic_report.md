# RePhraseAI – Academic Report (MCA Final-Year Project)

## 1. Abstract
RePhraseAI is a web-based Generative AI system that rewrites user text in nine styles while preserving meaning. A hybrid methodology compares sequence-to-sequence LSTM, BiLSTM and GRU models trained from scratch with a fine-tuned FLAN-T5 Transformer on a human-labelled paraphrase corpus (PAWS). Each output is evaluated with cosine similarity, BERTScore, BLEU, ROUGE and perplexity and explained through word-level changes. The system is delivered as a React + FastAPI application with JWT authentication and a persistent history.

## 2. Problem statement
Writers, students and professionals need to reword text for clarity, tone and originality. Manual rewriting is slow, and thesaurus-based tools replace words without understanding context, often changing meaning. A system is needed that generates fluent paraphrases, lets users control style and creativity, and *quantifies* how well the meaning was preserved.

## 3. Objectives
1. Prepare a genuine paraphrase dataset with a reproducible NLP preprocessing pipeline.
2. Implement LSTM/BiLSTM/GRU seq2seq models with attention.
3. Fine-tune/use a pretrained Transformer (FLAN-T5) for paraphrasing.
4. Design style-specific prompts.
5. Evaluate with multiple metrics and compare all models.
6. Provide explainability, history and a modern web interface; deploy locally.

## 4. Existing system
Rule/thesaurus-based synonym replacers; commercial paraphrasers that are closed black boxes and wrap external LLM APIs; RNN-based research prototypes with limited fluency. Limitations: context-blind substitutions, no similarity guarantees, no explanation of changes, no transparency about the model.

## 5. Proposed system
A pipeline: preprocessing → semantic encoding → generative decoding → post-processing → quality evaluation → explanation. Runs local open models, ranks multiple candidates by (semantic similarity, wording change), reports metrics and highlights changes, stores history per user.

## 6. Methodology
Dataset preparation → RNN experiments → Transformer fine-tuning → prompt engineering → evaluation → deployment (see `docs/methodology.md`).

## 7. System architecture
See `docs/architecture.md`: React → FastAPI → Auth → Preprocessing → GenAI service → Transformer → Evaluation → Database → Response.

## 8. Technologies used
React 18, Vite, Tailwind CSS, React Router, Recharts, jsPDF; Python, FastAPI, SQLAlchemy, SQLite/PostgreSQL, JWT (python-jose), bcrypt; PyTorch, Hugging Face Transformers/Datasets, SentencePiece, sentence-transformers, sacreBLEU, rouge-score, bert-score.

## 9. Dataset description
PAWS (Paraphrase Adversaries from Word Scrambling): sentence pairs with human labels (1 = paraphrase). We keep label-1 pairs, giving aligned source/target data suitable for supervised paraphrase generation. Alternatives supported: MRPC, Quora Question Pairs, ParaNMT (CSV). Cleaning, de-duplication and an 80/10/10 split are in `training/preprocessing.py`; counts are written to `data/processed/stats.json`.

## 10. Model architecture
*RNN models*: embedding → (Bi)LSTM/GRU encoder → Luong attention → RNN decoder → vocabulary softmax. *Transformer*: FLAN-T5 – stacked encoder with self-attention, decoder with masked self-attention and cross-attention, feed-forward layers, relative positional bias, SentencePiece vocabulary.

## 11. Training methodology
Cross-entropy loss, back-propagation, Adam (RNN) / AdamW (T5), learning rates 1e-3 / 3e-4, batch size 64 / 16, validation after every epoch, checkpoint of the best validation loss, CPU/GPU switch, gradient clipping, dropout, ReduceLROnPlateau / linear warm-up schedules.

## 12. Evaluation methodology
Reference-based BLEU, ROUGE-1/L, BERTScore on a held-out test split; semantic cosine similarity between source and output; perplexity (DistilGPT-2) for fluency; training time, validation loss and inference time for efficiency. A good paraphrase = high semantic similarity + sufficiently different wording.

## 13. Results
Run `python training/evaluate.py --samples 200 --include-zero-shot`; it writes `docs/results/comparison.csv`, `comparison.json`, `model_comparison.png` and `validation_loss_curves.png`. Paste your measured values here:

| Model | Train time (s) | Val loss | BLEU | ROUGE-L | BERTScore | Semantic sim. | Inference (ms) |
|---|---|---|---|---|---|---|---|
| LSTM | | | | | | | |
| BiLSTM | | | | | | | |
| GRU | | | | | | | |
| FLAN-T5 (fine-tuned) | | | | | | | |

*Expected qualitative trend (hypothesis to verify, not a measured result):* the Transformer should lead on BERTScore/semantic similarity and fluency; the RNNs train faster and infer faster but produce less fluent text with small data. Report whatever you measure, and discuss any deviation honestly.

## 14. Advantages
Open and local (no API dependency); contextual, fluent output; multiple styles; measurable quality; explainable; user history and dashboard; clean modular code; CPU-capable.

## 15. Limitations
Tuned on PAWS (conservative, high word overlap); RNN models are word-level with limited vocabulary; evaluation metrics approximate human judgement; CPU inference of FLAN-T5-base takes seconds; style control relies on prompts, so small models follow them imperfectly; tone/grammar modules are rule-based; English only.

## 16. Future scope
Fine-tune on style-labelled data or with LoRA on larger models (FLAN-T5-large, Llama); add reinforcement learning from similarity/diversity rewards; multilingual support; plagiarism checks; human-evaluation study; Docker/cloud deployment; browser extension; streaming generation.

## 17. Conclusion
RePhraseAI demonstrates the full GenAI lifecycle – data, classical and Transformer models, prompting, evaluation, explainability and deployment – and shows why attention-based pretrained models are better suited to contextual text generation than recurrent networks.

## 18. Viva / interview questions and answers
1. **What is paraphrasing and how is it different from summarisation?** Paraphrasing re-expresses the same content in different words; summarisation shortens content and drops detail.
2. **Why seq2seq?** Input and output are both variable-length sequences; an encoder compresses meaning and a decoder generates new wording.
3. **LSTM vs GRU?** LSTM has input/forget/output gates and a cell state; GRU merges them into update/reset gates, fewer parameters, usually faster, often similar accuracy.
4. **Why bidirectional encoder?** It reads left-to-right and right-to-left, so each position sees full-sentence context.
5. **What is attention?** A weighted sum of encoder states per decoding step; weights come from similarity of the decoder state with each encoder state; it removes the fixed-vector bottleneck.
6. **Why Transformers over RNNs?** Direct token-to-token connections, parallel training, better long-range context, large-scale pretraining.
7. **What is FLAN-T5?** T5 (text-to-text encoder-decoder) further fine-tuned on many instruction datasets, so it follows prompts like "rewrite formally".
8. **What does the tokenizer do?** SentencePiece splits text into subwords, mapping to ids; avoids OOV words.
9. **Why padding and attention masks?** Batches need equal length; masks stop attention (and loss) from using pad tokens.
10. **What loss do you use?** Token-level cross-entropy with pad/−100 ignored.
11. **What is teacher forcing?** Feeding the ground-truth previous token to the decoder during training for stable learning; my RNN trainer exposes a ratio.
12. **Explain temperature.** It scales logits before softmax; low = deterministic, high = diverse; 0 switches to beam search in my service.
13. **Beam search vs sampling?** Beam keeps the k best partial sequences (safe, repetitive); nucleus sampling draws from the top-p mass (varied).
14. **How is meaning preservation measured?** Cosine similarity of sentence embeddings and BERTScore.
15. **Why can BLEU be misleading for paraphrases?** Many valid paraphrases share few n-grams; and against the *original*, high BLEU means little rewriting.
16. **What does perplexity tell you?** How surprised a language model is by the text; lower = more fluent. It does not measure meaning.
17. **How did you avoid data leakage?** One reference per source sentence, de-duplicated before splitting with a fixed seed.
18. **Why PAWS?** Human-verified paraphrase pairs with word-order variation; weakness is high lexical overlap.
19. **How do you choose among multiple candidates?** Score = 0.7·similarity + 0.3·lexical change (capped), penalising copies.
20. **How is the system secured?** bcrypt-hashed passwords, JWT with expiry and jti, logout blacklist, user-scoped history queries, input length validation.
21. **Why FastAPI?** Async-capable, automatic OpenAPI docs, Pydantic validation, high performance.
22. **How would you scale it?** GPU inference server, model quantisation, request queue, caching, Docker/Kubernetes, PostgreSQL.
23. **How is this not just an API wrapper?** Data pipeline, from-scratch RNN training, fine-tuning, local inference, own evaluation and explainability layers.
24. **What are the ethical concerns?** Misuse for plagiarism/evasion of detectors, bias inherited from training data; mitigate with transparency and usage guidelines.
25. **What would you improve first?** Train on more diverse data (Quora/ParaNMT), larger model with LoRA, and human evaluation.
