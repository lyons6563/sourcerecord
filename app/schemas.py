from pydantic import BaseModel, HttpUrl


class SourceCreate(BaseModel):
    url: HttpUrl


class SourceOut(BaseModel):
    id: str
    url: str
    canonical_url: str


class CaptureOut(BaseModel):
    id: str
    source_id: str
    captured_at: str
    fetch_status: int
    raw_bytes_sha256: str
    normalized_text_sha256: str
    chain_sha256: str


class TimelineItem(BaseModel):
    id: str
    captured_at: str
    fetch_status: int
    raw_bytes_sha256: str
    normalized_text_sha256: str
    chain_sha256: str


class TimelineOut(BaseModel):
    source_id: str
    items: list[TimelineItem]
