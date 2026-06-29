"""
supercube-backend – FastAPI + SQLite
Highscore-Backend für das SuperCube Unity WebGL Spiel
Deploy auf Render.com als Web Service (Python)
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import os

# ── Config ──────────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./highscores.db")
ALLOWED_ORIGINS_RAW = os.getenv("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS = [o.strip() for o in ALLOWED_ORIGINS_RAW.split(",") if o.strip()] or ["*"]
TOP_N = int(os.getenv("TOP_N", "6"))  # Wie viele Einträge angezeigt werden

# Render.com: /data nur nutzen wenn Disk gemountet ist
if DATABASE_URL.startswith("sqlite") and os.path.isdir("/data") and os.access("/data", os.W_OK):
    DATABASE_URL = "sqlite:////data/highscores.db"

# ── DB ───────────────────────────────────────────────────────────────────────
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Highscore(Base):
    __tablename__ = "highscores"
    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(50), nullable=False)
    points     = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# ── Schemas ──────────────────────────────────────────────────────────────────
class HighscoreEntry(BaseModel):
    name: str
    points: int

class ScoreItem(BaseModel):
    name: str
    points: str  # String für Kompatibilität mit dem Unity-Code (der "-" erwartet)

class HighscoreResponse(BaseModel):
    scores: list[ScoreItem]

# ── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(title="SuperCube Highscore Backend", version="1.0.0")

# Drunterliegende Middleware-Konfiguration überschreiben:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if ALLOWED_ORIGINS == ["*"] else ALLOWED_ORIGINS,
    allow_credentials=False,  # Für WebGL-Requests auf False setzen!
    allow_methods=["*"],      # Erlaubt GET, POST, OPTIONS automatisch
    allow_headers=["*"],      # Erlaubt alle Header, die Unity mitsendet
)

# ── Routes ───────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"service": "supercube-backend", "version": "1.0.0", "docs": "/docs"}

@app.get("/highscores", response_model=HighscoreResponse)
def get_highscores():
    """Top-N Highscores lesen – kompatibel mit dem Unity MenuController"""
    db = SessionLocal()
    try:
        # Nutze text() für rohe SQL-Abfragen in SQLAlchemy
        query = text("""
            SELECT name, MAX(points) as points
            FROM highscores
            GROUP BY name
            ORDER BY points DESC
            LIMIT :n
        """)

        rows = db.execute(query, {"n": TOP_N}).fetchall()

        scores = [ScoreItem(name=r[0], points=str(r[1])) for r in rows]

        # Mit "-" auffüllen falls weniger als TOP_N Einträge
        while len(scores) < TOP_N:
            scores.append(ScoreItem(name="-", points="-"))

        return HighscoreResponse(scores=scores)
    except Exception as e:
        print(f"Fehler beim Laden der Highscores: {e}") # Zeigt den Fehler in den Render-Logs
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/highscores", status_code=201)
def set_highscore(entry: HighscoreEntry):
    """Highscore speichern – wird vom Unity GameOverController aufgerufen"""
    name = entry.name.strip()[:50]
    if not name:
        raise HTTPException(status_code=400, detail="Name darf nicht leer sein")
    if entry.points < 0:
        raise HTTPException(status_code=400, detail="Punkte müssen positiv sein")

    db = SessionLocal()
    try:
        score = Highscore(name=name, points=entry.points)
        db.add(score)
        db.commit()
        return {"status": "success", "message": "Highscore gespeichert", "name": name, "points": entry.points}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/highscores/all")
def get_all_highscores(limit: int = 100):
    """Alle Einträge – für Admin/Debug"""
    db = SessionLocal()
    try:
        rows = db.query(Highscore).order_by(Highscore.points.desc()).limit(limit).all()
        return [{"id": r.id, "name": r.name, "points": r.points,
                 "created_at": r.created_at.isoformat()} for r in rows]
    finally:
        db.close()

@app.delete("/highscores/{highscore_id}", status_code=204)
def delete_highscore(highscore_id: int, admin_key: str = ""):
    """Einzelnen Eintrag löschen (mit Admin-Key aus Env)"""
    expected = os.getenv("ADMIN_KEY", "")
    if expected and admin_key != expected:
        raise HTTPException(status_code=403, detail="Ungültiger Admin-Key")
    db = SessionLocal()
    try:
        entry = db.query(Highscore).filter(Highscore.id == highscore_id).first()
        if not entry:
            raise HTTPException(status_code=404, detail="Nicht gefunden")
        db.delete(entry)
        db.commit()
    finally:
        db.close()
