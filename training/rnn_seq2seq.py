"""LSTM / GRU / BiLSTM encoder-decoder (with Luong attention) for paraphrase generation.

Shows the classical seq2seq pipeline from scratch:
tokenisation -> vocabulary -> padding + masks -> encoder -> attention decoder ->
cross-entropy loss -> back-propagation -> Adam -> validation -> checkpointing.
"""
import argparse
import json
import re
import time
from collections import Counter
from pathlib import Path

import pandas as pd
import torch
import torch.nn as nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence, pad_sequence
from torch.utils.data import DataLoader, Dataset

ROOT = Path(__file__).resolve().parents[1]
PAD, SOS, EOS, UNK = 0, 1, 2, 3
TOKEN_RE = re.compile(r"\w+|[^\w\s]")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(str(text).lower())


class Vocab:
    def __init__(self, itos=None):
        self.itos = itos or ["<pad>", "<sos>", "<eos>", "<unk>"]
        self.stoi = {w: i for i, w in enumerate(self.itos)}

    @classmethod
    def build(cls, texts, min_freq=2, max_size=20000):
        counts = Counter(t for x in texts for t in tokenize(x))
        v = cls()
        for w, c in counts.most_common(max_size):
            if c >= min_freq:
                v.stoi[w] = len(v.itos); v.itos.append(w)
        return v

    def encode(self, text, add_sos_eos=False):
        ids = [self.stoi.get(t, UNK) for t in tokenize(text)]
        return [SOS] + ids + [EOS] if add_sos_eos else ids + [EOS]

    def decode(self, ids):
        words = []
        for i in ids:
            if i == EOS:
                break
            if i not in (PAD, SOS):
                words.append(self.itos[i])
        return re.sub(r"\s+([.,!?;:])", r"\1", " ".join(words)).strip()

    def __len__(self):
        return len(self.itos)


class PairDataset(Dataset):
    def __init__(self, df, vocab, max_len=64):
        self.src = [vocab.encode(s)[:max_len] for s in df.source]
        self.tgt = [vocab.encode(t, add_sos_eos=True)[:max_len + 2] for t in df.target]

    def __len__(self):
        return len(self.src)

    def __getitem__(self, i):
        return torch.tensor(self.src[i]), torch.tensor(self.tgt[i])


def collate(batch):
    """Padding: variable-length sequences -> rectangular tensors + lengths (used for masks)."""
    src, tgt = zip(*batch)
    lens = torch.tensor([len(s) for s in src])
    return pad_sequence(src, batch_first=True, padding_value=PAD), lens, pad_sequence(tgt, batch_first=True, padding_value=PAD)


class Encoder(nn.Module):
    def __init__(self, vocab, emb, hid, layers, cell, bidir, dropout):
        super().__init__()
        self.cell, self.dirs = cell, 2 if bidir else 1
        self.emb = nn.Embedding(vocab, emb, padding_idx=PAD)
        rnn = nn.LSTM if cell == "lstm" else nn.GRU
        self.rnn = rnn(emb, hid, layers, batch_first=True, bidirectional=bidir, dropout=dropout if layers > 1 else 0)
        self.fc = nn.Linear(hid * self.dirs, hid)
        self.drop = nn.Dropout(dropout)

    def _merge(self, h):                     # [layers*dirs,B,H] -> [layers,B,H]
        L = h.size(0) // self.dirs
        h = h.view(L, self.dirs, h.size(1), h.size(2))
        return torch.tanh(self.fc(torch.cat([h[:, i] for i in range(self.dirs)], dim=-1)))

    def forward(self, src, lens):
        x = self.drop(self.emb(src))
        packed = pack_padded_sequence(x, lens.cpu(), batch_first=True, enforce_sorted=False)
        out, state = self.rnn(packed)
        out, _ = pad_packed_sequence(out, batch_first=True, total_length=src.size(1))
        state = tuple(self._merge(s) for s in state) if self.cell == "lstm" else self._merge(state)
        return out, state


class Attention(nn.Module):
    """Luong 'general' attention with a padding mask."""
    def __init__(self, enc_dim, dec_dim):
        super().__init__()
        self.W = nn.Linear(enc_dim, dec_dim, bias=False)

    def forward(self, h, enc_out, mask):
        scores = torch.bmm(self.W(enc_out), h.unsqueeze(2)).squeeze(2).masked_fill(~mask, -1e9)
        w = torch.softmax(scores, dim=1)
        return torch.bmm(w.unsqueeze(1), enc_out).squeeze(1)


class Decoder(nn.Module):
    def __init__(self, vocab, emb, hid, layers, cell, enc_dim, dropout):
        super().__init__()
        self.emb = nn.Embedding(vocab, emb, padding_idx=PAD)
        rnn = nn.LSTM if cell == "lstm" else nn.GRU
        self.rnn = rnn(emb, hid, layers, batch_first=True, dropout=dropout if layers > 1 else 0)
        self.attn = Attention(enc_dim, hid)
        self.out = nn.Linear(hid + enc_dim, vocab)
        self.drop = nn.Dropout(dropout)

    def step(self, tok, state, enc_out, mask):
        o, state = self.rnn(self.drop(self.emb(tok)).unsqueeze(1), state)
        h = o.squeeze(1)
        return self.out(torch.cat([h, self.attn(h, enc_out, mask)], dim=1)), state


class Seq2Seq(nn.Module):
    def __init__(self, vocab, emb=256, hid=256, layers=1, cell="lstm", bidir=False, dropout=0.3):
        super().__init__()
        self.encoder = Encoder(vocab, emb, hid, layers, cell, bidir, dropout)
        self.decoder = Decoder(vocab, emb, hid, layers, cell, hid * (2 if bidir else 1), dropout)

    def forward(self, src, lens, tgt, teacher_forcing=1.0):
        mask = src != PAD
        enc_out, state = self.encoder(src, lens)
        tok, logits = tgt[:, 0], []
        for t in range(1, tgt.size(1)):
            step_logits, state = self.decoder.step(tok, state, enc_out, mask)
            logits.append(step_logits)
            use_tf = torch.rand(1).item() < teacher_forcing
            tok = tgt[:, t] if use_tf else step_logits.argmax(1)
        return torch.stack(logits, dim=1)               # [B, T-1, V]

    @torch.no_grad()
    def greedy(self, src, lens, max_len=64):
        mask = src != PAD
        enc_out, state = self.encoder(src, lens)
        tok = torch.full((src.size(0),), SOS, device=src.device)
        outs = []
        for _ in range(max_len):
            logits, state = self.decoder.step(tok, state, enc_out, mask)
            logits[:, UNK] = -1e9                        # never emit <unk>
            tok = logits.argmax(1)
            outs.append(tok)
        return torch.stack(outs, 1).tolist()


# ---------------- inference helpers (used by evaluate.py) ----------------
def load_rnn(model_dir: Path, device):
    cfg = json.loads((model_dir / "config.json").read_text())
    vocab = Vocab(json.loads((model_dir / "vocab.json").read_text()))
    model = Seq2Seq(len(vocab), cfg["emb"], cfg["hid"], cfg["layers"], cfg["cell"], cfg["bidir"], 0.0).to(device)
    model.load_state_dict(torch.load(model_dir / "model.pt", map_location=device))
    return model.eval(), vocab


@torch.no_grad()
def rnn_paraphrase(model, vocab, texts, device, batch_size=64):
    results = []
    for i in range(0, len(texts), batch_size):
        enc = [torch.tensor(vocab.encode(t)[:64]) for t in texts[i:i + batch_size]]
        lens = torch.tensor([len(e) for e in enc])
        src = pad_sequence(enc, batch_first=True, padding_value=PAD).to(device)
        results += [vocab.decode(ids) for ids in model.greedy(src, lens)]
    return results


# ---------------- training ----------------
def run_epoch(model, loader, loss_fn, device, optimizer=None, tf=1.0, clip=1.0):
    train = optimizer is not None
    model.train(train)
    total, n = 0.0, 0
    with torch.set_grad_enabled(train):
        for src, lens, tgt in loader:
            src, tgt = src.to(device), tgt.to(device)
            logits = model(src, lens, tgt, teacher_forcing=tf if train else 1.0)
            loss = loss_fn(logits.reshape(-1, logits.size(-1)), tgt[:, 1:].reshape(-1))   # ignores PAD
            if train:
                optimizer.zero_grad()
                loss.backward()                                  # back-propagation
                nn.utils.clip_grad_norm_(model.parameters(), clip)
                optimizer.step()                                 # parameter update
            total += loss.item(); n += 1
    return total / max(n, 1)


def main(default_cell="lstm"):
    p = argparse.ArgumentParser()
    p.add_argument("--cell", default=default_cell, choices=["lstm", "gru"])
    p.add_argument("--bidirectional", action="store_true", help="use a bidirectional encoder (BiLSTM)")
    p.add_argument("--epochs", type=int, default=10); p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--lr", type=float, default=1e-3); p.add_argument("--emb", type=int, default=256)
    p.add_argument("--hid", type=int, default=256); p.add_argument("--layers", type=int, default=1)
    p.add_argument("--dropout", type=float, default=0.3); p.add_argument("--max-train", type=int, default=None)
    p.add_argument("--device", default="auto", help="auto | cpu | cuda")
    args = p.parse_args()

    device = torch.device("cuda" if args.device == "auto" and torch.cuda.is_available() else
                          "cpu" if args.device == "auto" else args.device)
    name = "bilstm" if (args.cell == "lstm" and args.bidirectional) else args.cell
    out_dir = ROOT / "models" / name
    out_dir.mkdir(parents=True, exist_ok=True)

    train_df = pd.read_csv(ROOT / "data/train/train.csv")
    val_df = pd.read_csv(ROOT / "data/validation/validation.csv")
    if args.max_train:
        train_df = train_df.head(args.max_train)
    vocab = Vocab.build(list(train_df.source) + list(train_df.target))
    train_dl = DataLoader(PairDataset(train_df, vocab), args.batch_size, shuffle=True, collate_fn=collate)
    val_dl = DataLoader(PairDataset(val_df, vocab), args.batch_size, collate_fn=collate)

    model = Seq2Seq(len(vocab), args.emb, args.hid, args.layers, args.cell, args.bidirectional, args.dropout).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, factor=0.5, patience=1)
    loss_fn = nn.CrossEntropyLoss(ignore_index=PAD)
    print(f"[{name}] device={device} vocab={len(vocab)} params={n_params:,} train={len(train_df)} val={len(val_df)}")

    history, best, start = [], float("inf"), time.time()
    for epoch in range(1, args.epochs + 1):
        tr = run_epoch(model, train_dl, loss_fn, device, optimizer)
        va = run_epoch(model, val_dl, loss_fn, device)
        scheduler.step(va)
        history.append({"epoch": epoch, "train_loss": tr, "val_loss": va})
        print(f"epoch {epoch:02d} | train {tr:.4f} | val {va:.4f}")
        if va < best:                                              # model checkpointing
            best = va
            torch.save(model.state_dict(), out_dir / "model.pt")
    elapsed = time.time() - start

    (out_dir / "vocab.json").write_text(json.dumps(vocab.itos))
    (out_dir / "config.json").write_text(json.dumps({"emb": args.emb, "hid": args.hid, "layers": args.layers,
                                                     "cell": args.cell, "bidir": args.bidirectional}))
    (out_dir / "metrics.json").write_text(json.dumps({
        "model": name, "train_time_sec": elapsed, "best_val_loss": best, "parameters": n_params,
        "epochs": args.epochs, "batch_size": args.batch_size, "lr": args.lr, "device": str(device), "history": history}, indent=2))
    print(f"saved to {out_dir}  (train time {elapsed:.0f}s, best val loss {best:.4f})")


if __name__ == "__main__":
    main()
