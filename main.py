from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, Session, declarative_base

# --- Database Setup ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./escape_game.db"

# connect_args={"check_same_thread": False} is needed for SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# --- Database Model ---
class PlayerScore(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    time = Column(Float) # Time in seconds

# Create the database tables
Base.metadata.create_all(bind=engine)

# --- Pydantic Schemas ---
class ScoreCreate(BaseModel):
    name: str
    time: float

class Score(ScoreCreate):
    id: int

    class Config:
        from_attributes = True # updated for Pydantic v2 (was orm_mode = True)

# --- App Setup ---
app = FastAPI()

# Add CORS middleware to allow requests from your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Endpoints ---

@app.get("/")
def read_root():
    return {"message": "Escape Game API is running"}

@app.post("/scores/", response_model=Score)
def create_score(score: ScoreCreate, db: Session = Depends(get_db)):
    """
    Saves a new score for a player.
    """
    db_score = PlayerScore(name=score.name, time=score.time)
    db.add(db_score)
    db.commit()
    db.refresh(db_score)
    return db_score

@app.get("/scores/", response_model=list[Score])
def read_scores(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Returns a list of scores, ordered by time (ascending).
    """
    scores = db.query(PlayerScore).order_by(PlayerScore.time).offset(skip).limit(limit).all()
    return scores
