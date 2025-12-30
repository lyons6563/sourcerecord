import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import get_db
from app.models import Source, Capture
from app.schemas import TimelineOut, TimelineItem

router = APIRouter(prefix="/sources", tags=["timeline"])
V1_ORG_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

@router.get("/{source_id}/timeline", response_model=TimelineOut)
async def get_timeline(source_id: uuid.UUID, limit: int = 50, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Source).where(Source.id == source_id, Source.org_id == V1_ORG_ID))
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Source not found")

    rows = await db.execute(
        select(Capture)
        .where(Capture.source_id == source_id, Capture.org_id == V1_ORG_ID)
        .order_by(Capture.captured_at.desc())
        .limit(limit)
    )
    captures = rows.scalars().all()

    items = [
        TimelineItem(
            id=str(c.id),
            captured_at=c.captured_at.isoformat(),
            fetch_status=c.fetch_status,
            raw_bytes_sha256=c.raw_bytes_sha256,
            normalized_text_sha256=c.normalized_text_sha256,
            chain_sha256=c.chain_sha256,
        )
        for c in captures
    ]

    return TimelineOut(source_id=str(source_id), items=items)
