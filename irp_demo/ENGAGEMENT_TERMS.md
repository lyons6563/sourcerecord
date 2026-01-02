# Engagement Terms — SEC Inquiry Response Pack

## Scope of Engagement

This engagement provides one-time generation of a deterministic SEC Inquiry Response Pack from client-provided electronic communications export data (e.g., email, collaboration tools). The service consists of processing input files through a documented methodology to produce a ZIP file containing a PDF response document, evidence summaries, methodology documentation, and verification tools.

This is a one-time artifact generation service. It does not include ongoing monitoring, supervision, compliance review, or legal analysis.

## Client Responsibilities

The client is responsible for:
- Providing input files (email_export.csv and slack_export.json) in the specified format
- Ensuring input files are complete and accurate to the best of the client's knowledge
- Defining the scope of the inquiry, including time period, custodians, and communication systems
- Reviewing and approving the output before any use or attachment to regulatory responses
- Obtaining appropriate legal and compliance review of the output

Input files are provided by the client "as-is" without warranty as to completeness or accuracy.

## What Is Explicitly Excluded

This engagement does not include:
- Compliance determinations or assessments
- Legal analysis or advice
- Completeness verification of input data
- Ongoing services or support
- Modifications to the output after initial generation
- Reprocessing with revised inputs or changes (requires revised inputs and a new engagement)
- Interpretation of regulatory requirements
- Supervision or monitoring functions

## Data Handling and Retention

Input data provided by the client will be used solely for the purpose of generating the response pack. Data will be destroyed or returned to the client upon completion of the engagement, unless otherwise agreed in writing. No copies will be retained except as required by law or as explicitly agreed.

The client retains all rights to input data and output deliverables.

## Deliverables

The deliverable consists of a single ZIP file containing:
- Response_Pack.pdf (main response document)
- manifest.json (SHA256 hashes for verification)
- methodology.md (documentation of process)
- verify.py (verification script)
- evidence/email_summary.csv (sanitized email summary)
- evidence/slack_summary.json (sanitized Slack summary)

Outputs document the scope and process applied to the provided inputs only. They do not represent findings, conclusions, or assessments.

## Timing and Termination

The engagement begins upon receipt of required input files and payment terms as agreed. The engagement terminates upon delivery of the output ZIP file, unless otherwise specified.

Either party may terminate this engagement with written notice. Upon termination, any data will be returned or destroyed as specified above.

## No Legal or Compliance Advice

This engagement does not constitute legal advice, compliance advice, or regulatory guidance. The output is a factual compilation of processed data based on the methodology described in the deliverables.

Interpretation and use of the output, including any decision to attach it to a regulatory response, is the sole responsibility of the client's counsel or compliance personnel. The client should obtain appropriate legal and compliance review before any use.

No representations or warranties are made regarding the suitability of the output for any particular purpose or regulatory requirement.

