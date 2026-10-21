from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel


class HistoryItem(BaseModel):
    id: int
    original_text: str
    rephrased_text: str
    style: str
    model: str
    temperature: float | None = None
    similarity_score: float | None = None
    metrics: Optional[dict[str, Any]] = None
    explanation: Optional[dict[str, Any]] = None
    is_favorite: bool
    created_at: datetime
    model_config = {"from_attributes": True}
