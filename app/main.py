from fastapi import FastAPI

from app.routers import sources

app = FastAPI(title="SourceRecord", version="0.1.0")

app.include_router(sources.router)

@app.get("/health")
def health():
    return {"ok": True}
