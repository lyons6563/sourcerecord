#!/usr/bin/env python3
"""
Smoke test script for Proof Pack generation.
Generates a Proof Pack, writes it to disk, unzips it, and prints contents.
"""
import json
import zipfile
from pathlib import Path
from datetime import datetime, timezone

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.proofpack.builder import build_proof_pack



def main():
    # Ensure ./tmp exists
    tmp_dir = Path("./tmp")
    tmp_dir.mkdir(exist_ok=True)
    
    # Generate Proof Pack
    print("Generating Proof Pack...")
    zip_bytes, zip_filename = build_proof_pack("demo-source")
    
    # Write ZIP to ./tmp/<zip_filename>
    zip_path = tmp_dir / zip_filename
    zip_path.write_bytes(zip_bytes)
    print(f"✓ ZIP written to: {zip_path}")
    
    # Create extract directory with timestamp
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    extract_dir = tmp_dir / f"unzipped_{timestamp_str}"
    extract_dir.mkdir(exist_ok=True)
    print(f"✓ Extract directory: {extract_dir}")
    
    # Unzip to extract directory
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    
    # Get extracted file list
    extracted_files = sorted(extract_dir.iterdir())
    print(f"\nExtracted files ({len(extracted_files)}):")
    for file_path in extracted_files:
        print(f"  - {file_path.name}")
    
    # Read and parse manifest.json
    manifest_path = extract_dir / "manifest.json"
    if manifest_path.exists():
        manifest_content = manifest_path.read_text(encoding='utf-8')
        manifest_data = json.loads(manifest_content)
        
        print(f"\nmanifest.json contents (pretty printed):")
        print(json.dumps(manifest_data, indent=2, sort_keys=True))
    else:
        print("\n⚠ manifest.json not found in extracted files")
    
    print(f"\n✓ Smoke test complete!")
    print(f"  ZIP: {zip_path}")
    print(f"  Extract: {extract_dir}")


if __name__ == "__main__":
    main()

