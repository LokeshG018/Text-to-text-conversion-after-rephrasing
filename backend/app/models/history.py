from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from app.database import Base
from app.models.user import utcnow


class RephraseHistory(Base):
    __tablename__ = "rephrase_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    original_text = Column(Text, nullable=False)
    rephrased_text = Column(Text, nullable=False)
    style = Column(String(30), nullable=False)
    model = Column(String(80), nullable=False)
    temperature = Column(Float, default=0.7)
    similarity_score = Column(Float)
    metrics = Column(JSON)          # BLEU, ROUGE, BERTScore, perplexity ...
    explanation = Column(JSON)      # word changes, structure notes
    is_favorite = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, index=True)
