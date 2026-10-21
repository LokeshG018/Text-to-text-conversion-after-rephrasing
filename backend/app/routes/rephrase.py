import json
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import RephraseHistory, User
from app.schemas.rephrase import EvaluateRequest, RephraseRequest, RephraseResponse
from app.services import analysis_service as analysis
from app.services.evaluation_service import evaluation_service
from app.services.preprocessing import clean_text
from app.services.prompt_service import STYLE_DESCRIPTIONS, build_prompt
from app.services.rephrase_service import rank_candidates, rephrase_service
from app.utils.deps import get_optional_user

router = APIRouter(prefix="/api", tags=["rephrase"])


@router.get("/health")
def health():
    return {"status": "ok", "model_loaded": rephrase_service.model is not None}


@router.get("/styles")
def styles():
    return [{"id": k, "description": v} for k, v in STYLE_DESCRIPTIONS.items()]


@router.post("/rephrase", response_model=RephraseResponse)
def rephrase(req: RephraseRequest, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    """Pipeline: preprocess -> prompt -> generate -> post-process -> evaluate -> explain -> store."""
    timings = {}
    t = time.perf_counter()
    text = clean_text(req.text)                                   # 1. preprocessing
    if len(text.split()) < 3:
        raise HTTPException(422, "Please enter at least 3 words")
    timings["preprocess"] = (time.perf_counter() - t) * 1000

    t = time.perf_counter()
    candidates, model_label = rephrase_service.generate(text, req.style, req.temperature, req.num_results)  # 2-5
    timings["generation"] = (time.perf_counter() - t) * 1000

    t = time.perf_counter()
    scored = [(c, evaluation_service.semantic_similarity(text, c)) for c in candidates]
    best_i = rank_candidates(text, scored)
    best, sim = scored[best_i]
    timings["ranking"] = (time.perf_counter() - t) * 1000

    t = time.perf_counter()
    metrics = evaluation_service.evaluate(text, best) if req.evaluate else {"semantic_similarity": round(sim, 4)}
    timings["evaluation"] = (time.perf_counter() - t) * 1000

    explanation = analysis.explain(text, best, sim)
    stats = {"original": analysis.text_stats(text), "rephrased": analysis.text_stats(best),
             "prompt_used": build_prompt("{input_text}", req.style)}
    cand_out = []
    for i, (c, s) in enumerate(scored):
        d = analysis.diff_words(text, c)
        d.pop("changes", None)
        cand_out.append({"text": c, "similarity": round(s, 4), "is_best": i == best_i, "diff": d})
    cand_out.sort(key=lambda x: not x["is_best"])

    history_id = None
    if user is not None:
        row = RephraseHistory(user_id=user.id, original_text=text, rephrased_text=best, style=req.style,
                              model=model_label, temperature=req.temperature, similarity_score=round(sim, 4),
                              metrics=metrics, explanation=explanation)
        db.add(row); db.commit(); db.refresh(row)
        history_id = row.id

    return RephraseResponse(original_text=text, rephrased_text=best, style=req.style, model=model_label,
                            temperature=req.temperature, similarity_score=round(sim, 4), candidates=cand_out,
                            metrics=metrics, explanation=explanation, stats=stats,
                            timings_ms={k: round(v, 1) for k, v in timings.items()}, history_id=history_id)


@router.post("/evaluate")
def evaluate(req: EvaluateRequest):
    metrics = evaluation_service.evaluate(req.original_text, req.rephrased_text, req.reference_text)
    return {"metrics": metrics, "explanation": analysis.explain(req.original_text, req.rephrased_text,
                                                                 metrics["semantic_similarity"])}


@router.post("/grammar")
def grammar(payload: dict):
    fixed, fixes = analysis.grammar_fix(payload.get("text", ""))
    return {"corrected_text": fixed, "fixes": fixes}


@router.get("/models/comparison")
def model_comparison():
    """Results written by training/evaluate.py (LSTM vs GRU vs Transformer)."""
    f = settings.COMPARISON_FILE
    if not f.exists():
        return {"available": False, "models": []}
    return {"available": True, **json.loads(f.read_text())}
