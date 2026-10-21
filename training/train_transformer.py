"""Fine-tune FLAN-T5 (encoder-decoder Transformer) for paraphrasing with Hugging Face.

  python train_transformer.py --model google/flan-t5-small --epochs 3 --max-train 20000
  python train_transformer.py --model google/flan-t5-base --epochs 3 --batch-size 8 --device cuda
Saves to models/flan-t5-paraphrase (auto-detected by the backend).
"""
import argparse
import json
import time
from pathlib import Path

import pandas as pd
import torch
from datasets import Dataset
from transformers import (AutoModelForSeq2SeqLM, AutoTokenizer, DataCollatorForSeq2Seq,
                          Seq2SeqTrainer, Seq2SeqTrainingArguments)

ROOT = Path(__file__).resolve().parents[1]
# Must match backend/app/services/prompt_service.py -> build_prompt(text, "standard")
PROMPT = ("Rephrase the following text while preserving its original meaning. "
          "Change the wording and sentence structure, and avoid unnecessary changes.\n\nText: {text}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="google/flan-t5-small")
    p.add_argument("--epochs", type=int, default=3); p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--lr", type=float, default=3e-4); p.add_argument("--weight-decay", type=float, default=0.01)
    p.add_argument("--max-len", type=int, default=128); p.add_argument("--max-train", type=int, default=None)
    p.add_argument("--device", default="auto", help="auto | cpu | cuda")
    args = p.parse_args()

    use_cuda = torch.cuda.is_available() and args.device in ("auto", "cuda")
    tok = AutoTokenizer.from_pretrained(args.model)                      # SentencePiece tokenizer
    model = AutoModelForSeq2SeqLM.from_pretrained(args.model)

    train_df = pd.read_csv(ROOT / "data/train/train.csv")
    val_df = pd.read_csv(ROOT / "data/validation/validation.csv")
    if args.max_train:
        train_df = train_df.head(args.max_train)

    def encode(batch):
        x = tok([PROMPT.format(text=s) for s in batch["source"]], max_length=args.max_len * 2, truncation=True)
        y = tok(text_target=batch["target"], max_length=args.max_len, truncation=True)
        x["labels"] = y["input_ids"]          # attention masks are produced by the tokenizer
        return x

    cols = ["source", "target"]
    train_ds = Dataset.from_pandas(train_df[cols]).map(encode, batched=True, remove_columns=cols)
    val_ds = Dataset.from_pandas(val_df[cols]).map(encode, batched=True, remove_columns=cols)
    collator = DataCollatorForSeq2Seq(tok, model=model, label_pad_token_id=-100)   # dynamic padding

    out_dir = ROOT / "models" / "flan-t5-paraphrase"
    targs = Seq2SeqTrainingArguments(
        output_dir=str(ROOT / "models" / "checkpoints"), num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size, per_device_eval_batch_size=args.batch_size,
        learning_rate=args.lr, weight_decay=args.weight_decay, lr_scheduler_type="linear", warmup_ratio=0.05,
        eval_strategy="epoch", save_strategy="epoch", save_total_limit=2,       # checkpointing
        load_best_model_at_end=True, metric_for_best_model="eval_loss", greater_is_better=False,
        logging_steps=50, fp16=use_cuda, use_cpu=not use_cuda, report_to="none")
    trainer = Seq2SeqTrainer(model=model, args=targs, train_dataset=train_ds, eval_dataset=val_ds,
                             data_collator=collator, processing_class=tok)       # AdamW + cross-entropy inside

    start = time.time()
    trainer.train()                                                          # forward, loss, backward, optimiser step
    elapsed = time.time() - start
    eval_metrics = trainer.evaluate()
    trainer.save_model(str(out_dir)); tok.save_pretrained(str(out_dir))

    history = [h for h in trainer.state.log_history]
    (out_dir / "metrics.json").write_text(json.dumps({
        "model": "transformer", "base_model": args.model, "train_time_sec": elapsed,
        "best_val_loss": eval_metrics["eval_loss"], "parameters": sum(p.numel() for p in model.parameters()),
        "epochs": args.epochs, "batch_size": args.batch_size, "lr": args.lr,
        "device": "cuda" if use_cuda else "cpu", "history": history}, indent=2))
    print(f"Saved fine-tuned model to {out_dir}  (time {elapsed:.0f}s, val loss {eval_metrics['eval_loss']:.4f})")


if __name__ == "__main__":
    main()
