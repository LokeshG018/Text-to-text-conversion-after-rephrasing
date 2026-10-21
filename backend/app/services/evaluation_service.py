"""Quality evaluation: cosine similarity, BLEU, ROUGE, BERTScore, perplexity."""
import math
import threading

import torch

from app.config import settings
from app.services.analysis_service import lexical_change
from app.utils.device import get_device


class EvaluationService:
    def __init__(self):
        self._lock = threading.Lock()
        self._embedder = None
        self._rouge = None
        self._bert = None
        self._lm = None
        self._lm_tok = None
        self.device = None

    # ---------- lazy loaders ----------
    def _dev(self):
        if self.device is None:
            self.device = get_device(settings.DEVICE)
        return self.device

    def _get_embedder(self):
        with self._lock:
            if self._embedder is None:
                from sentence_transformers import SentenceTransformer
                self._embedder = SentenceTransformer(settings.EMBEDDING_MODEL, device=str(self._dev()))
        return self._embedder

    def _get_rouge(self):
        if self._rouge is None:
            from rouge_score import rouge_scorer
            self._rouge = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
        return self._rouge

    def _get_bert(self):
        with self._lock:
            if self._bert is None:
                from bert_score import BERTScorer
                self._bert = BERTScorer(model_type=settings.BERTSCORE_MODEL, lang="en", device=str(self._dev()))
        return self._bert

    def _get_lm(self):
        with self._lock:
            if self._lm is None:
                from transformers import AutoModelForCausalLM, AutoTokenizer
                self._lm_tok = AutoTokenizer.from_pretrained(settings.PERPLEXITY_MODEL)
                self._lm = AutoModelForCausalLM.from_pretrained(settings.PERPLEXITY_MODEL).to(self._dev()).eval()
        return self._lm, self._lm_tok

    # ---------- metrics ----------
    def semantic_similarity(self, a: str, b: str) -> float:
        """Cosine similarity between sentence embeddings (0..1)."""
        from sentence_transformers import util
        emb = self._get_embedder().encode([a, b], convert_to_tensor=True, normalize_embeddings=True)
        return float(max(0.0, min(1.0, util.cos_sim(emb[0], emb[1]).item())))

    @staticmethod
    def bleu(reference: str, hypothesis: str) -> float:
        import sacrebleu
        return sacrebleu.sentence_bleu(hypothesis, [reference]).score / 100.0

    def rouge(self, reference: str, hypothesis: str) -> dict:
        s = self._get_rouge().score(reference, hypothesis)
        return {"rouge1": s["rouge1"].fmeasure, "rouge2": s["rouge2"].fmeasure, "rougeL": s["rougeL"].fmeasure}

    def bertscore(self, reference: str, hypothesis: str) -> float:
        _, _, f1 = self._get_bert().score([hypothesis], [reference])
        return float(f1[0])

    @torch.inference_mode()
    def perplexity(self, text: str) -> float:
        """Fluency of the rephrased text under a causal LM (lower = more fluent)."""
        lm, tok = self._get_lm()
        enc = tok(tok.bos_token + text, return_tensors="pt", truncation=True, max_length=512).to(self._dev())
        loss = lm(**enc, labels=enc["input_ids"]).loss
        return float(math.exp(min(loss.item(), 20)))

    # ---------- combined ----------
    def evaluate(self, original: str, rephrased: str, reference: str | None = None) -> dict:
        ref = reference or original
        rouge = self.rouge(ref, rephrased)
        sim = self.semantic_similarity(original, rephrased)
        change = lexical_change(original, rephrased)
        result = {
            "semantic_similarity": round(sim, 4),
            "bleu": round(self.bleu(ref, rephrased), 4),
            "rouge1": round(rouge["rouge1"], 4),
            "rouge2": round(rouge["rouge2"], 4),
            "rougeL": round(rouge["rougeL"], 4),
            "lexical_change": round(change, 4),
            "reference": "provided reference" if reference else "original text",
        }
        if settings.ENABLE_BERTSCORE:
            try:
                result["bertscore_f1"] = round(self.bertscore(original, rephrased), 4)
            except Exception as exc:  # model download failure etc.
                result["bertscore_f1"] = None
                result["bertscore_error"] = str(exc)[:120]
        try:
            result["perplexity"] = round(self.perplexity(rephrased), 2)
        except Exception as exc:
            result["perplexity"] = None
            result["perplexity_error"] = str(exc)[:120]
        result["verdict"] = verdict(sim, change)
        return result


def verdict(sim: float, change: float) -> str:
    """A good paraphrase = high semantic similarity + sufficiently different wording."""
    if sim >= 0.85 and change >= 0.25:
        return "Excellent paraphrase: meaning preserved with clearly different wording"
    if sim >= 0.80 and change < 0.25:
        return "Meaning preserved but wording is very close to the original"
    if sim >= 0.70:
        return "Acceptable paraphrase: minor meaning drift possible"
    return "Low similarity: the meaning may have changed"


evaluation_service = EvaluationService()
