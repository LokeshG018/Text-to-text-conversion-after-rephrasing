# Methodology

## Dataset
Default: **PAWS (labeled_final)** – human-labelled sentence pairs; only `label=1` (true paraphrases) are kept. Alternatives: MRPC (`--dataset mrpc`), Quora Question Pairs or ParaNMT via `--dataset csv`.
*Why suitable:* aligned (source, paraphrase) pairs = supervised seq2seq training signal; PAWS pairs share vocabulary but differ in word order, forcing models to learn structure rather than word swapping. *Limitation:* high lexical overlap, so BLEU against the reference is high and paraphrases are conservative; Quora/ParaNMT give more lexical diversity.

Pipeline (`training/preprocessing.py`): null removal → Unicode/whitespace/de-tokenisation normalisation → remove identical pairs → length filter (4–60 words) → duplicate pair removal → one reference per source (prevents train/test leakage) → 80/10/10 split (seeded). Statistics are saved to `data/processed/stats.json`.

## LSTM / BiLSTM / GRU (`training/rnn_seq2seq.py`)
Word-level vocabulary (min freq 2, ≤20k) → embeddings → (Bi)LSTM or GRU encoder with packed sequences → Luong attention with padding mask → RNN decoder → softmax over vocabulary. Loss: cross-entropy ignoring PAD. Optimiser: Adam (lr 1e-3, ReduceLROnPlateau), gradient clipping 1.0, dropout 0.3, best-validation checkpointing, greedy decoding.

## Transformer (`training/train_transformer.py`)
FLAN-T5 (SentencePiece tokenizer, encoder-decoder, relative position bias, instruction-tuned). Inputs are built with the same prompt template the backend uses; labels are padded with −100; `DataCollatorForSeq2Seq` pads dynamically; Hugging Face `Seq2SeqTrainer` runs AdamW (lr 3e-4, weight decay 0.01, linear schedule, warm-up), evaluates each epoch, keeps the best checkpoint by validation loss. CPU/GPU via `--device`, fp16 on CUDA.

## Why Transformers beat RNNs for contextual generation
1. Self-attention gives O(1) path length between any two tokens (RNN: O(n)) → better long-range dependencies, no vanishing-gradient bottleneck.
2. Training parallelises across tokens; RNNs are sequential.
3. Large-scale pretraining + instruction tuning transfers grammar, world knowledge and the ability to follow style prompts; our RNNs learn from one dataset only.
4. Subword tokenisation removes the out-of-vocabulary problem.

## Evaluation
Reference-based (test set, `evaluate.py`): BLEU (sacreBLEU), ROUGE-1/L, BERTScore-F1 (DistilBERT). Source-based: cosine similarity of `all-MiniLM-L6-v2` embeddings (meaning preservation). Efficiency: training time, validation loss, inference ms/sample. Online (per request): semantic similarity, BERTScore, BLEU/ROUGE vs original, perplexity (DistilGPT-2), lexical change.
Interpretation: a good paraphrase has **high semantic similarity and BERTScore with moderately low BLEU/ROUGE against the original**. High BLEU against the original means the model merely copied.
Caveat: when comparing models against the dataset *reference*, high BLEU is good; when comparing a paraphrase to its *original*, high BLEU is bad. The app reports the latter and labels it.

## Prompt engineering
Nine templates in `prompt_service.py` (e.g. professional, academic). Each states the task, tone, and constraints ("preserve meaning", "avoid introducing new information"). Temperature/top-p control diversity; `no_repeat_ngram_size=3` limits repetition; a retry is triggered if the model copies the input.
