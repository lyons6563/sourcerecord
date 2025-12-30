from fastapi import FastAPI
from app.routers.sources import router as sources_router
from app.routers.captures import router as captures_router
from app.routers.timelines import router as timelines_router

app = FastAPI(title="SourceRecord", version="0.1.0")

app.include_router(sources_router)
app.include_router(captures_router)
app.include_router(timelines_router)

@app.get("/health")
def health():
    return {"ok": True}
