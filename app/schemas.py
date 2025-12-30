from pydantic import BaseModel, HttpUrl

class SourceCreate(BaseModel):
    url: HttpUrl

class SourceOut(BaseModel):
    id: str
    url: str
    canonical_url: str
