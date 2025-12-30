import hashlib
import io
import json
from datetime import datetime, timezone
from typing import Tuple
import zipfile


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


def build_proof_pack(source_id: str) -> Tuple[bytes, str]:
    """
    Generate an in-memory Proof Pack ZIP containing manifest.json, timeline.json, methodology.md, and verify.py.
    
    Args:
        source_id: The source ID to include in the pack
        
    Returns:
        Tuple of (zip_bytes, zip_filename) where:
        - zip_bytes: The complete ZIP file as bytes
        - zip_filename: Filename in format proofpack_<source_id>_<YYYYMMDDTHHMMSSZ>.zip
    """
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
        
        # 1. Generate timeline.json (minimal placeholder)
        timeline_data = {
            "source_id": source_id,
            "captures": []
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
            "capture_count": 0,
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

