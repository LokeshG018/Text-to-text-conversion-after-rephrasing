"""FastAPI application entry point.  Run:  uvicorn app.main:app --reload --port 8000"""
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401  (register ORM tables)
from app.config import settings
from app.database import Base, engine
from app.routes import auth, history, rephrase
from app.services.rephrase_service import rephrase_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    if settings.WARMUP_ON_STARTUP:
        threading.Thread(target=rephrase_service.load, daemon=True).start()
    yield


app = FastAPI(title="RePhraseAI API", version="1.0.0",
              description="GenAI text rephrasing with FLAN-T5, semantic evaluation and explainability",
              lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router)
app.include_router(rephrase.router)
app.include_router(history.router)


@app.get("/")
def root():
    return {"app": "RePhraseAI", "docs": "/docs"}
