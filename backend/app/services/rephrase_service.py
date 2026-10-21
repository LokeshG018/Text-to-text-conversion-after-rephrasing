"""Generative rephrasing with a (fine-tuned) FLAN-T5 encoder-decoder Transformer."""
import re
import threading

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from app.config import settings
from app.services.analysis_service import grammar_fix, lexical_change
from app.services.preprocessing import chunk_sentences
from app.services.prompt_service import build_prompt
from app.utils.device import get_device


class RephraseService:
    def __init__(self):
        self._lock = threading.Lock()
        self.tokenizer = None
        self.model = None
        self.device = None
        self.label = "FLAN-T5"

    # ---------- model loading ----------
    def load(self):
        if self.model is not None:
            return
        with self._lock:
            if self.model is not None:
                return
            ft = settings.FINETUNED_MODEL_DIR
            if ft.exists() and (ft / "config.json").exists():
                source, self.label = str(ft), "FLAN-T5 (fine-tuned)"
            else:
                source = settings.MODEL_NAME
                self.label = source.split("/")[-1].upper()
            self.device = get_device(settings.DEVICE)
            self.tokenizer = AutoTokenizer.from_pretrained(source)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(source).to(self.device).eval()

    # ---------- generation ----------
    @torch.inference_mode()
    def _generate_chunk(self, chunk: str, style: str, temperature: float, n: int) -> list[str]:
        prompt = build_prompt(chunk, style)
        enc = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512).to(self.device)
        in_len = len(self.tokenizer(chunk)["input_ids"])
        factor = {"concise": 0.8, "expand": 2.2}.get(style, 1.5)
        max_new = int(min(400, max(32, in_len * factor + 10)))

        def run(temp: float) -> list[str]:
            kw = dict(max_new_tokens=max_new, num_return_sequences=n, no_repeat_ngram_size=3)
            if temp <= 0.05:           # deterministic beam search
                kw.update(do_sample=False, num_beams=max(4, n), early_stopping=True)
            else:                      # nucleus sampling, creativity controlled by temperature
                kw.update(do_sample=True, temperature=temp, top_p=0.92, top_k=50, repetition_penalty=1.1)
            out = self.model.generate(**enc, **kw)
            return [self.tokenizer.decode(o, skip_special_tokens=True).strip() for o in out]

        outs = run(temperature)
        # if the model just copied the input, retry once with more randomness
        if all(o.lower() == chunk.lower() for o in outs):
            outs = run(min(1.3, max(temperature, 0.5) + 0.4))
        return outs

    def generate(self, text: str, style: str = "standard", temperature: float = 0.7,
                 num_results: int = 1) -> tuple[list[str], str]:
        self.load()
        per_chunk = [self._generate_chunk(c, style, temperature, num_results) for c in chunk_sentences(text)]
        candidates = []
        for i in range(num_results):
            joined = " ".join(c[i % len(c)] for c in per_chunk)
            candidates.append(self.postprocess(joined, text))
        return candidates, self.label

    # ---------- post-processing ----------
    @staticmethod
    def postprocess(output: str, original: str) -> str:
        output = re.sub(r"^(text|rephrased( text)?|output)\s*:\s*", "", output.strip(), flags=re.I)
        output = re.sub(r"\s+", " ", output)
        output, _ = grammar_fix(output)
        if original.rstrip()[-1:] in ".!?" and output[-1:] not in ".!?":
            output += original.rstrip()[-1]
        return output


def rank_candidates(original: str, scored: list[tuple[str, float]]) -> int:
    """Pick the best candidate: high semantic similarity AND sufficient wording change."""
    best_i, best_score = 0, -1.0
    for i, (text, sim) in enumerate(scored):
        change = lexical_change(original, text)
        score = 0.7 * sim + 0.3 * min(change, 0.6)
        if text.strip().lower() == original.strip().lower():
            score -= 0.5
        if score > best_score:
            best_i, best_score = i, score
    return best_i


rephrase_service = RephraseService()
