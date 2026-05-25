from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, matches, predictions, leaderboard, competitions

app = FastAPI(title="CM Predictor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(matches.router, prefix="/api/matches", tags=["matches"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["predictions"])
app.include_router(leaderboard.router, prefix="/api/leaderboard", tags=["leaderboard"])
app.include_router(competitions.router, prefix="/api/competitions", tags=["competitions"])


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/admin/init-db")
def admin_init_db():
    from app.database import init_db, fetchall
    try:
        init_db()
        comps = fetchall("SELECT id, name FROM competitions ORDER BY name")
        return {"status": "ok", "competitions_count": len(comps), "competitions": comps}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
