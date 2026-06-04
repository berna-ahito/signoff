from fastapi import FastAPI

from app.routers import ai_reviews, approvals, audit, auth, requests, users

app = FastAPI(title="ProcureFlow AI", version="0.1.0")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(requests.router)
app.include_router(approvals.router)
app.include_router(audit.router)
app.include_router(ai_reviews.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}
