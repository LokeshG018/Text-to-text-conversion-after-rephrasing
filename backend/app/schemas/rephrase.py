from typing import Any, Literal, Optional
from pydantic import BaseModel, Field

Style = Literal["standard", "professional", "simple", "academic", "creative",
                "formal", "casual", "concise", "expand"]


class RephraseRequest(BaseModel):
    text: str = Field(min_length=3, max_length=5000)
    style: Style = "standard"
    temperature: float = Field(0.7, ge=0.0, le=1.5)
    num_results: int = Field(1, ge=1, le=3)
    evaluate: bool = True


class Candidate(BaseModel):
    text: str
    similarity: float
    is_best: bool = False
    diff: dict[str, Any]


class RephraseResponse(BaseModel):
    original_text: str
    rephrased_text: str
    style: str
    model: str
    temperature: float
    similarity_score: float
    candidates: list[Candidate]
    metrics: dict[str, Any] = {}
    explanation: dict[str, Any] = {}
    stats: dict[str, Any] = {}
    timings_ms: dict[str, float] = {}
    history_id: Optional[int] = None


class EvaluateRequest(BaseModel):
    original_text: str = Field(min_length=1)
    rephrased_text: str = Field(min_length=1)
    reference_text: Optional[str] = None
