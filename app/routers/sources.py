import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import get_db
from app.models import Source, EventLog
from app.schemas import SourceCreate, SourceOut
from app.services.normalize import canonicalize_url

router = APIRouter(prefix="/sources", tags=["sources"])

# v1: single org hard-coded
V1_ORG_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

@router.post("", response_model=SourceOut)
async def create_source(payload: SourceCreate, db: AsyncSession = Depends(get_db)):
    canonical = canonicalize_url(str(payload.url))

    existing = await db.execute(
        select(Source).where(Source.org_id == V1_ORG_ID, Source.canonical_url == canonical)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Source already exists")

    s = Source(
        org_id=V1_ORG_ID,
        url=str(payload.url),
        canonical_url=canonical,
        title=None,
        created_by=None,
    )
    db.add(s)
    await db.flush()  # get s.id

    db.add(
        EventLog(
            org_id=V1_ORG_ID,
            actor_user_id=None,
            event_type="source.created",
            entity_type="source",
            entity_id=s.id,
            payload={"url": s.url, "canonical_url": s.canonical_url},
        )
    )

    await db.commit()
    return SourceOut(id=str(s.id), url=s.url, canonical_url=s.canonical_url)
