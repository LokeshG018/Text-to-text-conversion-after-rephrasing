"""Compare LSTM vs BiLSTM vs GRU vs Transformer on the held-out test set.

  python evaluate.py --samples 200 [--include-zero-shot]
Creates docs/results/comparison.json (read by the web app), comparison.csv and PNG graphs.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rnn_seq2seq import load_rnn, rnn_paraphrase  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "results"


def t5_predictor(path_or_name, device, batch=16):
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    from train_transformer import PROMPT
    tok = AutoTokenizer.from_pretrained(path_or_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(path_or_name).to(device).eval()

    @torch.no_grad()
    def predict(texts):
        outs = []
        for i in range(0, len(texts), batch):
            enc = tok([PROMPT.format(text=t) for t in texts[i:i + batch]], return_tensors="pt",
                      padding=True, truncation=True, max_length=256).to(device)
            gen = model.generate(**enc, max_new_tokens=96, num_beams=4, no_repeat_ngram_size=3)
            outs += tok.batch_decode(gen, skip_special_tokens=True)
        return outs
    return predict


def score(sources, refs, preds):
    import sacrebleu
    from bert_score import BERTScorer
    from rouge_score import rouge_scorer
    from sentence_transformers import SentenceTransformer, util
    bleu = sacrebleu.corpus_bleu(preds, [refs]).score / 100
    rs = rouge_scorer.RougeScorer(["rouge1", "rougeL"], use_stemmer=True)
    r1 = sum(rs.score(r, p)["rouge1"].fmeasure for r, p in zip(refs, preds)) / len(preds)
    rl = sum(rs.score(r, p)["rougeL"].fmeasure for r, p in zip(refs, preds)) / len(preds)
    _, _, f1 = BERTScorer(model_type="distilbert-base-uncased", lang="en").score(preds, refs)
    st = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    a = st.encode(sources, convert_to_tensor=True, normalize_embeddings=True)
    b = st.encode(preds, convert_to_tensor=True, normalize_embeddings=True)
    sim = util.cos_sim(a, b).diag().mean().item()
    return {"bleu": bleu, "rouge1": r1, "rougeL": rl, "bertscore_f1": f1.mean().item(), "semantic_similarity": sim}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--samples", type=int, default=200)
    p.add_argument("--include-zero-shot", action="store_true", help="also score un-tuned FLAN-T5-small")
    p.add_argument("--device", default="auto")
    args = p.parse_args()
    device = torch.device("cuda" if args.device == "auto" and torch.cuda.is_available() else
                          "cpu" if args.device == "auto" else args.device)

    test = pd.read_csv(ROOT / "data/test/test.csv").head(args.samples)
    sources, refs = test.source.tolist(), test.target.tolist()
    OUT.mkdir(parents=True, exist_ok=True)

    runners = {}
    for name in ["lstm", "bilstm", "gru"]:
        d = ROOT / "models" / name
        if (d / "model.pt").exists():
            m, v = load_rnn(d, device)
            runners[name] = (lambda t, m=m, v=v: rnn_paraphrase(m, v, t, device), d / "metrics.json")
    ft = ROOT / "models" / "flan-t5-paraphrase"
    if (ft / "config.json").exists():
        runners["transformer"] = (t5_predictor(str(ft), device), ft / "metrics.json")
    if args.include_zero_shot:
        runners["flan-t5-zero-shot"] = (t5_predictor("google/flan-t5-small", device), None)
    if not runners:
        sys.exit("No trained models found in models/. Run the training scripts first.")

    rows = []
    for name, (predict, metrics_file) in runners.items():
        print(f"Evaluating {name} on {len(sources)} test pairs ...")
        t0 = time.time()
        preds = predict(sources)
        infer_ms = (time.time() - t0) / len(sources) * 1000
        row = {"model": name, "inference_ms_per_sample": infer_ms, **score(sources, refs, preds)}
        if metrics_file and metrics_file.exists():
            m = json.loads(metrics_file.read_text())
            row.update(train_time_sec=m["train_time_sec"], val_loss=m["best_val_loss"], parameters=m["parameters"])
        row["example"] = {"source": sources[0], "prediction": preds[0], "reference": refs[0]}
        rows.append(row)

    (OUT / "comparison.json").write_text(json.dumps({"samples": len(sources), "models": rows}, indent=2))
    pd.DataFrame([{k: v for k, v in r.items() if k != "example"} for r in rows]).to_csv(OUT / "comparison.csv", index=False)
    plot(rows)
    print(pd.DataFrame([{k: v for k, v in r.items() if k != "example"} for r in rows]).round(4).to_string(index=False))


def plot(rows):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    names = [r["model"] for r in rows]
    panels = [("bleu", "BLEU"), ("rougeL", "ROUGE-L"), ("bertscore_f1", "BERTScore F1"), ("semantic_similarity", "Semantic similarity"),
              ("train_time_sec", "Training time (s)"), ("val_loss", "Validation loss"), ("inference_ms_per_sample", "Inference (ms/sample)")]
    fig, axes = plt.subplots(2, 4, figsize=(18, 8))
    for ax, (key, title) in zip(axes.flat, panels):
        vals = [r.get(key) or 0 for r in rows]
        ax.bar(names, vals, color=["#6366f1", "#8b5cf6", "#06b6d4", "#10b981", "#f59e0b"][:len(names)])
        ax.set_title(title); ax.tick_params(axis="x", rotation=30)
    axes.flat[-1].axis("off")
    plt.tight_layout(); plt.savefig(OUT / "model_comparison.png", dpi=150); plt.close()

    plt.figure(figsize=(7, 4))
    for n in names:
        f = ROOT / "models" / n / "metrics.json"
        if n == "transformer" or not f.exists():
            f = ROOT / "models" / "flan-t5-paraphrase" / "metrics.json" if n == "transformer" else f
        if f.exists():
            h = json.loads(f.read_text())["history"]
            if h and "val_loss" in h[0]:
                plt.plot([x["epoch"] for x in h], [x["val_loss"] for x in h], marker="o", label=n)
    plt.xlabel("epoch"); plt.ylabel("validation loss"); plt.legend(); plt.title("RNN validation loss per epoch")
    plt.tight_layout(); plt.savefig(OUT / "validation_loss_curves.png", dpi=150); plt.close()


if __name__ == "__main__":
    main()
