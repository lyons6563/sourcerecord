import hashlib
import httpx
from bs4 import BeautifulSoup

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def normalize_html_to_text(html: bytes) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    text = " ".join(text.split())
    return text.strip()

async def fetch_url(url: str, timeout_s: int = 30) -> dict:
    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout_s) as client:
        r = await client.get(url, headers={"User-Agent": "SourceRecord/0.1"})
    raw = r.content
    norm_text = normalize_html_to_text(raw).encode("utf-8")

    return {
        "status": r.status_code,
        "headers": dict(r.headers),
        "content_type": r.headers.get("content-type"),
        "etag": r.headers.get("etag"),
        "last_modified": r.headers.get("last-modified"),
        "raw_bytes": raw,
        "raw_bytes_sha256": sha256_hex(raw),
        "normalized_text": norm_text.decode("utf-8"),
        "normalized_text_sha256": sha256_hex(norm_text),
        "normalized_text_len": len(norm_text),
    }
