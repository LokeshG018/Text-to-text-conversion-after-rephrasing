from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import RephraseHistory, User
from app.schemas.history import HistoryItem
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("", response_model=list[HistoryItem])
def list_history(favorites_only: bool = False, search: str | None = None, limit: int = Query(50, le=200),
                 skip: int = 0, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(RephraseHistory).filter(RephraseHistory.user_id == user.id)
    if favorites_only:
        q = q.filter(RephraseHistory.is_favorite.is_(True))
    if search:
        like = f"%{search}%"
        q = q.filter(RephraseHistory.original_text.ilike(like) | RephraseHistory.rephrased_text.ilike(like))
    return q.order_by(RephraseHistory.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/stats/summary")
def summary(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(RephraseHistory).filter(RephraseHistory.user_id == user.id).all()
    sims = [r.similarity_score for r in rows if r.similarity_score is not None]
    return {
        "total": len(rows),
        "favorites": sum(r.is_favorite for r in rows),
        "avg_similarity": round(sum(sims) / len(sims), 4) if sims else None,
        "styles": dict(Counter(r.style for r in rows)),
        "words_processed": sum(len(r.original_text.split()) for r in rows),
        "recent_similarity": [{"id": r.id, "similarity": r.similarity_score}
                              for r in sorted(rows, key=lambda r: r.created_at)[-20:]],
    }


def _own(db, user, item_id):
    row = db.get(RephraseHistory, item_id)
    if not row or row.user_id != user.id:
        raise HTTPException(404, "History item not found")
    return row


@router.patch("/{item_id}/favorite", response_model=HistoryItem)
def toggle_favorite(item_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = _own(db, user, item_id)
    row.is_favorite = not row.is_favorite
    db.commit(); db.refresh(row)
    return row


@router.delete("/{item_id}")
def delete_item(item_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.delete(_own(db, user, item_id)); db.commit()
    return {"deleted": item_id}
