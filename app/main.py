from fastapi import FastAPI

app = FastAPI(title="ProcureFlow AI", version="0.1.0")


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}
