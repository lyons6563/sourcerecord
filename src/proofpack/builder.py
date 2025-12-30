import asyncio
import hashlib
import io
import json
import uuid
from datetime import datetime, timezone
from typing import Tuple
import zipfile
from sqlalchemy import select

from app.db import AsyncSessionLocal
from app.models import Source, Capture


def _assert_manifest_data_small(manifest_data: dict) -> None:
    """Internal guard to prevent large data in manifest."""
    manifest_str = json.dumps(manifest_data, sort_keys=True)
    assert len(manifest_str) < 10000, "Manifest data too large - may contain file contents"
    # Ensure no bytes objects
    for key, value in manifest_data.items():
        assert not isinstance(value, bytes), f"Manifest contains bytes at key: {key}"
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    for k, v in item.items():
                        assert not isinstance(v, bytes), f"Manifest contains bytes at {key}[].{k}"


V1_ORG_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


async def build_proof_pack(source_id: str, limit: int = 50) -> Tuple[bytes, str]:
    """
    Generate an in-memory Proof Pack ZIP containing manifest.json, timeline.json, methodology.md, and verify.py.
    
    Args:
        source_id: The source ID to include in the pack
        limit: Maximum number of captures to include in timeline (default 50)
        
    Returns:
        Tuple of (zip_bytes, zip_filename) where:
        - zip_bytes: The complete ZIP file as bytes
        - zip_filename: Filename in format proofpack_<source_id>_<YYYYMMDDTHHMMSSZ>.zip
    """
    # Parse source_id to UUID
    source_uuid = uuid.UUID(source_id)
    
    # Open database session
    async with AsyncSessionLocal() as db:
        # Validate source exists for V1_ORG_ID and get canonical_url
        source_res = await db.execute(
            select(Source).where(Source.id == source_uuid, Source.org_id == V1_ORG_ID)
        )
        source = source_res.scalar_one_or_none()
        if not source:
            raise ValueError(f"Source {source_id} not found for V1_ORG_ID")
        canonical_url = source.canonical_url
        
        # Fetch Capture rows for source/org ordered by captured_at asc with limit
        captures_res = await db.execute(
            select(Capture)
            .where(Capture.source_id == source_uuid, Capture.org_id == V1_ORG_ID)
            .order_by(Capture.captured_at.asc())
            .limit(limit)
        )
        captures = captures_res.scalars().all()
        
        # Build timeline items with all required fields
        items = [
            {
                "id": str(c.id),
                "prev_capture_id": str(c.prev_capture_id) if c.prev_capture_id else None,
                "captured_at": c.captured_at.isoformat(),
                "canonical_url": canonical_url,
                "raw_bytes_sha256": c.raw_bytes_sha256,
                "normalized_text_sha256": c.normalized_text_sha256,
                "chain_sha256": c.chain_sha256,
            }
            for c in captures
        ]
    
    # Generate timestamp for filename
    now = datetime.now(timezone.utc)
    timestamp_str = now.strftime("%Y%m%dT%H%M%SZ")
    zip_filename = f"proofpack_{source_id}_{timestamp_str}.zip"
    
    # Create in-memory ZIP
    zip_buffer = io.BytesIO()
    
    # Use deterministic ZIP settings
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Generate files in fixed order for determinism
        files_data = []
        
        # 1. Generate timeline.json with real data
        timeline_data = {
            "source_id": source_id,
            "items": items
        }
        timeline_json = json.dumps(timeline_data, sort_keys=True, indent=2)
        timeline_bytes = timeline_json.encode('utf-8')
        timeline_sha256 = hashlib.sha256(timeline_bytes).hexdigest()
        zip_file.writestr("timeline.json", timeline_bytes)
        files_data.append({"path": "timeline.json", "sha256": timeline_sha256})
        
        # 2. Generate methodology.md
        methodology_content = "# Methodology\n\nThis Proof Pack contains source verification data.\n"
        methodology_bytes = methodology_content.encode('utf-8')
        methodology_sha256 = hashlib.sha256(methodology_bytes).hexdigest()
        zip_file.writestr("methodology.md", methodology_bytes)
        files_data.append({"path": "methodology.md", "sha256": methodology_sha256})
        
        # 3. Generate verify.py (deterministic, no timestamps)
        verify_py_content = """#!/usr/bin/env python3
import hashlib
import json
import sys
from pathlib import Path

def main():
    # Verify all files listed in manifest.json by SHA256
    manifest_path = Path("manifest.json")
    if not manifest_path.exists():
        print("FAIL: manifest.json not found")
        sys.exit(1)
    
    with open(manifest_path, "rb") as f:
        manifest_data = json.loads(f.read().decode("utf-8"))
    
    files = manifest_data.get("files", [])
    for file_entry in files:
        file_path = Path(file_entry["path"])
        expected_hash = file_entry["sha256"]
        
        if not file_path.exists():
            print(f"FAIL: {file_path} not found")
            sys.exit(1)
        
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        
        computed_hash = hashlib.sha256(file_bytes).hexdigest()
        
        if computed_hash != expected_hash:
            print(f"FAIL: {file_path} hash mismatch")
            sys.exit(1)
    
    print("PASS: all files verified")
    
    # Verify capture hash chain using timeline.json items
    timeline_path = Path("timeline.json")
    if not timeline_path.exists():
        sys.exit(0)
    
    with open(timeline_path, "rb") as f:
        timeline_data = json.loads(f.read().decode("utf-8"))
    
    items = timeline_data.get("items", [])
    if not items:
        sys.exit(0)
    
    # Check if chain_sha256 fields are missing
    has_chain_sha256 = any(item.get("chain_sha256") is not None for item in items)
    if not has_chain_sha256:
        print("SKIP: timeline items missing chain_sha256; not verifying chain")
        sys.exit(0)
    
    # Replay chain verification
    prev_chain = None
    
    for idx, item in enumerate(items):
        item_id = item.get("id")
        prev_capture_id = item.get("prev_capture_id")
        captured_at_iso = item.get("captured_at")
        canonical_url = item.get("canonical_url")
        raw_sha = item.get("raw_bytes_sha256")
        norm_sha = item.get("normalized_text_sha256")
        chain_sha256 = item.get("chain_sha256")
        
        # Validate required fields
        if not item_id:
            print(f"FAIL: item[{idx}] missing id")
            sys.exit(1)
        if captured_at_iso is None:
            print(f"FAIL: item[{idx}] missing captured_at")
            sys.exit(1)
        if canonical_url is None:
            print(f"FAIL: item[{idx}] missing canonical_url")
            sys.exit(1)
        if raw_sha is None:
            print(f"FAIL: item[{idx}] missing raw_bytes_sha256")
            sys.exit(1)
        if norm_sha is None:
            print(f"FAIL: item[{idx}] missing normalized_text_sha256")
            sys.exit(1)
        if chain_sha256 is None:
            print(f"FAIL: item[{idx}] missing chain_sha256")
            sys.exit(1)
        
        # Validate prev_capture_id linkage
        if idx == 0:
            # First item should have no prev_capture_id
            if prev_capture_id is not None:
                print(f"FAIL: item[{idx}] prev_capture_id should be null for first item")
                sys.exit(1)
        else:
            # Subsequent items must have prev_capture_id matching previous item's id
            prev_item_id = items[idx - 1].get("id")
            if prev_capture_id != prev_item_id:
                print(f"FAIL: item[{idx}] prev_capture_id {prev_capture_id} does not match previous item id {prev_item_id}")
                sys.exit(1)
        
        # Recompute chain hash using exact algorithm
        chain_input = "|".join([
            prev_capture_id or "",
            prev_chain or "",
            raw_sha,
            norm_sha,
            captured_at_iso,
            canonical_url,
        ])
        computed_chain = hashlib.sha256(chain_input.encode("utf-8")).hexdigest()
        
        if computed_chain != chain_sha256:
            print(f"FAIL: item[{idx}] chain_sha256 mismatch (computed {computed_chain}, expected {chain_sha256})")
            sys.exit(1)
        
        prev_chain = chain_sha256
    
    print("PASS: timeline capture hash chain verified")
    sys.exit(0)

if __name__ == "__main__":
    main()
"""
        verify_py_bytes = verify_py_content.encode('utf-8')
        verify_py_sha256 = hashlib.sha256(verify_py_bytes).hexdigest()
        zip_file.writestr("verify.py", verify_py_bytes)
        files_data.append({"path": "verify.py", "sha256": verify_py_sha256})
        
        # 4. Generate manifest.json (metadata only, no file contents, no self-reference)
        generated_at = now.isoformat()
        # Create manifest structure with only metadata and hashes (excludes manifest.json itself)
        manifest_data = {
            "source_id": str(source_id),
            "generated_at": generated_at,
            "hash_algo": "sha256",
            "capture_count": len(items),
            "files": files_data
        }
        
        # Guard: ensure manifest is small and contains no raw bytes
        _assert_manifest_data_small(manifest_data)
        
        # Generate manifest.json (no self-hash, no loop needed)
        manifest_json = json.dumps(manifest_data, sort_keys=True, indent=2)
        manifest_bytes = manifest_json.encode('utf-8')
        zip_file.writestr("manifest.json", manifest_bytes)
    
    # Get the complete ZIP bytes
    zip_bytes = zip_buffer.getvalue()
    
    return zip_bytes, zip_filename


def build_proof_pack_sync(source_id: str, limit: int = 50) -> Tuple[bytes, str]:
    """
    Synchronous wrapper for build_proof_pack for use in scripts.
    
    Args:
        source_id: The source ID to include in the pack
        limit: Maximum number of captures to include in timeline (default 50)
        
    Returns:
        Tuple of (zip_bytes, zip_filename) where:
        - zip_bytes: The complete ZIP file as bytes
        - zip_filename: Filename in format proofpack_<source_id>_<YYYYMMDDTHHMMSSZ>.zip
    """
    return asyncio.run(build_proof_pack(source_id, limit))

