"""Dataset preparation: download -> clean -> dedupe -> normalise -> split.

Usage:
  python preprocessing.py --dataset paws              # PAWS (labeled_final), label==1 pairs
  python preprocessing.py --dataset mrpc              # MSR Paraphrase Corpus (GLUE), label==1 pairs
  python preprocessing.py --dataset csv --csv path.csv --src-col question1 --tgt-col question2 --label-col is_duplicate
                                                      # e.g. Quora Question Pairs from Kaggle
Output: data/raw, data/processed/all.csv, data/{train,validation,test}/*.csv, data/processed/stats.json
"""
import argparse
import json
import re
import unicodedata
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def load_raw(args) -> pd.DataFrame:
    if args.dataset == "csv":
        df = pd.read_csv(args.csv)
        out = pd.DataFrame({"source": df[args.src_col], "target": df[args.tgt_col]})
        if args.label_col:
            out = out[df[args.label_col] == 1]
        return out
    from datasets import concatenate_datasets, load_dataset
    if args.dataset == "paws":
        ds = load_dataset("google-research-datasets/paws", "labeled_final")
        df = concatenate_datasets([ds[s] for s in ds]).to_pandas()
    elif args.dataset == "mrpc":
        ds = load_dataset("nyu-mll/glue", "mrpc")
        df = concatenate_datasets([ds[s] for s in ds]).to_pandas()
    else:
        raise ValueError(args.dataset)
    df = df[df["label"] == 1]                         # keep true paraphrase pairs only
    return df.rename(columns={"sentence1": "source", "sentence2": "target"})[["source", "target"]]


def normalise(text: str) -> str:
    text = unicodedata.normalize("NFKC", str(text))
    text = re.sub(r"\s+([.,!?;:%)])", r"\1", text)       # PAWS/MRPC are tokenised: "word ." -> "word."
    text = re.sub(r"([(\$])\s+", r"\1", text)
    text = re.sub(r"\s+'s\b", "'s", text)
    text = text.replace(" n't", "n't").replace("`` ", '"').replace(" ''", '"').replace("-lrb-", "(").replace("-rrb-", ")")
    text = re.sub(r"\s+", " ", text).strip()
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    return text


def clean(df: pd.DataFrame, min_words: int, max_words: int) -> pd.DataFrame:
    stats = {"raw_pairs": len(df)}
    df = df.dropna(subset=["source", "target"]).copy()                       # null removal
    stats["after_null_removal"] = len(df)
    df["source"] = df["source"].map(normalise)                               # normalisation
    df["target"] = df["target"].map(normalise)
    df = df[(df.source != "") & (df.target != "")]
    df = df[df.source.str.lower() != df.target.str.lower()]                  # identical pairs teach copying
    n = lambda s: s.str.split().str.len()
    df = df[n(df.source).between(min_words, max_words) & n(df.target).between(min_words, max_words)]
    stats["after_length_filter"] = len(df)
    df = df.drop_duplicates(subset=["source", "target"])                     # duplicate removal
    df = df.drop_duplicates(subset=["source"])                               # one reference per source (prevents leakage)
    stats["after_duplicate_removal"] = len(df)
    return df.reset_index(drop=True), stats


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", default="paws", choices=["paws", "mrpc", "csv"])
    p.add_argument("--csv"); p.add_argument("--src-col", default="source"); p.add_argument("--tgt-col", default="target")
    p.add_argument("--label-col", default=None)
    p.add_argument("--min-words", type=int, default=4); p.add_argument("--max-words", type=int, default=60)
    p.add_argument("--max-samples", type=int, default=None, help="subsample for quick CPU experiments")
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    for d in ["raw", "processed", "train", "validation", "test"]:
        (DATA / d).mkdir(parents=True, exist_ok=True)

    raw = load_raw(args)
    raw.to_csv(DATA / "raw" / f"{args.dataset}_pairs_raw.csv", index=False)
    df, stats = clean(raw, args.min_words, args.max_words)
    if args.max_samples and len(df) > args.max_samples:
        df = df.sample(args.max_samples, random_state=args.seed).reset_index(drop=True)
    df.to_csv(DATA / "processed" / "all.csv", index=False)

    train, rest = train_test_split(df, test_size=0.2, random_state=args.seed)         # 80 / 10 / 10
    val, test = train_test_split(rest, test_size=0.5, random_state=args.seed)
    train.to_csv(DATA / "train" / "train.csv", index=False)
    val.to_csv(DATA / "validation" / "validation.csv", index=False)
    test.to_csv(DATA / "test" / "test.csv", index=False)

    stats.update({"dataset": args.dataset, "final_pairs": len(df), "train": len(train),
                  "validation": len(val), "test": len(test),
                  "avg_source_words": round(df.source.str.split().str.len().mean(), 2),
                  "avg_target_words": round(df.target.str.split().str.len().mean(), 2)})
    (DATA / "processed" / "stats.json").write_text(json.dumps(stats, indent=2))
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
