import hashlib
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import get_db
from app.models import Source, Capture, CaptureArtifact, EventLog
from app.schemas import CaptureOut
from app.services.fetcher import fetch_url

router = APIRouter(prefix="/sources", tags=["captures"])

V1_ORG_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def compute_chain_sha256(
    prev_capture_id: str | None,
    prev_chain: str | None,
    raw_sha: str,
    norm_sha: str,
    captured_at_iso: str,
    canonical_url: str,
) -> str:
    base = "|".join(
        [
            prev_capture_id or "",
            prev_chain or "",
            raw_sha,
            norm_sha,
            captured_at_iso,
            canonical_url,
        ]
    )
    return sha256_hex(base.encode("utf-8"))


@router.post("/{source_id}/captures", response_model=CaptureOut)
async def create_capture(source_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    # Load source
    res = await db.execute(
        select(Source).where(Source.id == source_id, Source.org_id == V1_ORG_ID)
    )
    source = res.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    # Find previous capture for chain linking
    prev = await db.execute(
        select(Capture)
        .where(Capture.source_id == source_id, Capture.org_id == V1_ORG_ID)
        .order_by(Capture.captured_at.desc())
        .limit(1)
    )
    prev_cap = prev.scalar_one_or_none()
    prev_chain = prev_cap.chain_sha256 if prev_cap else None
    prev_id = prev_cap.id if prev_cap else None

    captured_at = datetime.now(timezone.utc)
    captured_at_iso = captured_at.isoformat()

    try:
        fetched = await fetch_url(source.canonical_url)
        fetch_status = int(fetched["status"])
        fetch_error = None
    except Exception as e:
        # Append-only failure event (still a capture row)
        fetched = {
            "headers": {},
            "content_type": None,
            "etag": None,
            "last_modified": None,
            "raw_bytes_sha256": sha256_hex(b""),
            "normalized_text_sha256": sha256_hex(b""),
            "normalized_text_len": 0,
            "normalized_text": "",
        }
        fetch_status = 0
        fetch_error = repr(e)

    chain_sha = compute_chain_sha256(
        prev_capture_id=str(prev_id) if prev_id else None,
        prev_chain=prev_chain,
        raw_sha=fetched["raw_bytes_sha256"],
        norm_sha=fetched["normalized_text_sha256"],
        captured_at_iso=captured_at_iso,
        canonical_url=source.canonical_url,
    )


    cap = Capture(
        org_id=V1_ORG_ID,
        source_id=source_id,
        captured_at=captured_at,
        fetch_status=fetch_status,
        fetch_error=fetch_error,
        content_type=fetched.get("content_type"),
        etag=fetched.get("etag"),
        last_modified=fetched.get("last_modified"),
        response_headers=fetched.get("headers"),
        raw_bytes_sha256=fetched["raw_bytes_sha256"],
        normalized_text_sha256=fetched["normalized_text_sha256"],
        normalized_text_len=int(fetched["normalized_text_len"]),
        prev_capture_id=prev_id,
        chain_sha256=chain_sha,
    )
    db.add(cap)
    await db.flush()

    # v1 artifacts: store local placeholders (S3 later)
    # we keep DB shape stable now
    db.add_all([
        CaptureArtifact(
            capture_id=cap.id,
            kind="raw",
            bucket="local",
            object_key=f"data/artifacts/{cap.id}/raw.bin",
            bytes=0,
            sha256=fetched["raw_bytes_sha256"],
        ),
        CaptureArtifact(
            capture_id=cap.id,
            kind="text",
            bucket="local",
            object_key=f"data/artifacts/{cap.id}/text.txt",
            bytes=0,
            sha256=fetched["normalized_text_sha256"],
        ),
    ])

    db.add(
        EventLog(
            org_id=V1_ORG_ID,
            actor_user_id=None,
            event_type="capture.created" if fetch_error is None else "capture.failed",
            entity_type="capture",
            entity_id=cap.id,
            payload={"source_id": str(source_id), "fetch_status": fetch_status},
        )
    )

    await db.commit()

    return CaptureOut(
        id=str(cap.id),
        source_id=str(source_id),
        captured_at=captured_at_iso,
        fetch_status=fetch_status,
        raw_bytes_sha256=cap.raw_bytes_sha256,
        normalized_text_sha256=cap.normalized_text_sha256,
        chain_sha256=cap.chain_sha256,
    )
