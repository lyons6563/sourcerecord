# Running the SEC Inquiry Response Pack

## Overview

This process generates a deterministic SEC Inquiry Response Pack ZIP file from email and Slack export data. The output may be attached to a regulatory response at the discretion of counsel or compliance.

## When This Should Be Used

Use this process only in response to an active SEC inquiry or examination request with a defined scope. The scope should specify the time period, custodians, and communication systems to be included.

## What This Does Not Do

This process does not:
- Make compliance determinations or assessments
- Guarantee completeness of communications reviewed
- Provide supervision or monitoring functions
- Replace legal or compliance review

Final review and use of the output, including any attachment to a regulatory response, is the responsibility of counsel or compliance personnel.

## Prerequisites

- Python 3.8 or higher installed
- `reportlab` package installed (`pip install reportlab`)

## Required Inputs

Place the following files in `irp_demo/data/`:

- `email_export.csv` - Email communications export with columns: message_id, timestamp, sender, recipients, subject, body, has_attachment, custodian
- `slack_export.json` - Slack workspace export in the specified JSON format

## Folder Structure

```
irp_demo/
├── data/              # Input files go here
│   ├── email_export.csv
│   └── slack_export.json
├── scripts/
│   └── generate_irp_demo.py
└── out/               # Output ZIP file created here
    └── SEC_Response_Pack_Demo.zip
```

## Execution

From the project root directory, run:

```bash
python irp_demo/scripts/generate_irp_demo.py
```

## Expected Outputs

The script generates `irp_demo/out/SEC_Response_Pack_Demo.zip` containing:

- `Response_Pack.pdf` - Main response document
- `manifest.json` - SHA256 hashes for all files
- `methodology.md` - Methodology documentation
- `verify.py` - Verification script
- `evidence/email_summary.csv` - Sanitized email summary
- `evidence/slack_summary.json` - Sanitized Slack summary

The console output includes:
- FILE_SHA256 report for each file
- Final ZIP SHA256 hash for verification

## Operator Guidelines

**Do:**
- Verify input files are in the correct location before running
- Confirm the ZIP SHA256 hash matches across multiple runs (determinism check)
- Extract and review the PDF before attachment to any response
- Run `verify.py` from the extracted ZIP to confirm file integrity
- Obtain appropriate legal or compliance review before use

**Do Not:**
- Modify input files after generation (re-run with original inputs if changes needed)
- Edit the generated ZIP contents directly
- Attach to a response without reviewing the PDF contents
- Assume the pack represents a complete review (scope is limited to provided inputs)

## Verification

After extraction, run the included verification script:

```bash
python verify.py
```

This confirms all files match their manifest hashes.

