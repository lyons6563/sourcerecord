# SourceRecord

v1: Capture public web pages (URLs) into an append-only statement timeline and proof pack.

Hard rules:
- Append-only event log (no deletes/edits)
- Public web URLs only
- Output: Statement Timeline + Proof Pack (ZIP + PDF)

## Independent Verification (Proof Pack)

Each Proof Pack ZIP contains: `manifest.json`, `timeline.json`, `verify.py`.

The `verify.py` script performs:
- SHA-256 file integrity check vs `manifest.json`
- Recomputes and verifies the append-only capture hash chain from `timeline.json`

No DB access. No network calls. If any file or timeline entry is modified, verification FAILS.

**How to verify:**
```bash
unzip proofpack.zip
cd proofpack
python verify.py
```
