from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import ai_reviews, approvals, audit, auth, requests, users

app = FastAPI(title="ProcureFlow AI", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(requests.router)
app.include_router(approvals.router)
app.include_router(audit.router)
app.include_router(ai_reviews.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}
