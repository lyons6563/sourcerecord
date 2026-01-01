1. Demo scenario (locked)

Regulatory context (plain, realistic):

An SEC exam request seeking a sample of advisor communications related to client recommendations during a defined period.

No enforcement drama. No whistleblower. No crypto.
This must feel routine but stressful.

Firm profile (fictional):

Mid-sized SEC-registered investment adviser

~15–30 advisors

Uses Microsoft 365 for email

Uses Slack internally

Written supervisory procedures in place

Trigger condition (explicit):

Active SEC request with a response deadline

This is not hypothetical usage.
The pack exists because the clock is running.

2. Scope parameters (exact)

These will appear verbatim in the PDF.

Time window

Start: January 1, 2024

End: February 15, 2024

Timezone: Eastern Time (ET)

Custodians (3 total)

Advisor A (lead advisor)

Advisor B (associate)

Supervisor C (principal / reviewer)

No firm-wide claims. No completeness theater.

Systems reviewed

Email (Microsoft 365 export, CSV)

Slack (Standard JSON export)

That’s it.
No Teams. No texts. No personal devices.

3. Fake data to generate (keep this boring and believable)
Email dataset

~120–180 total messages

Spread unevenly across custodians

Include:

Client emails

Internal advisor discussions

A few attachments

A few forwards/replies

Slack dataset

~200–300 messages

2 channels:

#advisors

#client-questions

Include:

Casual internal language

A few “take this offline” / “email me” type phrases

Light supervision chatter

Seeded keywords (very important)

Use these sparingly:

“gmail”

“personal email”

“send later”

“recommend”

“allocation”

“performance”

Nothing incriminating.
Nothing clever.
Just enough to justify categories existing.

4. Findings model (NO judgments)

The Response Pack never says:

compliant

non-compliant

violation

deficiency

breach

Instead, it reports categories and counts only.

Example categories (locked)

Messages referencing client recommendations

Messages containing attachments

Messages referencing non-firm communication channels

Messages containing portfolio or allocation language

Messages involving supervisory personnel

These categories are descriptive, not evaluative.

5. Explicit exclusions (this is a feature, not a weakness)

These must be stated clearly in the PDF:

No review of communications outside the stated time window

No review of personal devices or personal email accounts

No review of SMS, WhatsApp, or other messaging platforms

No assessment of advice suitability or regulatory compliance

No determination of recordkeeping completeness beyond provided exports

This is how the artifact reduces follow-up questions.

6. Response Pack ZIP structure (final)
SEC_Response_Pack_Demo/
├── Response_Pack.pdf
├── manifest.json
├── methodology.md
├── verify.py
└── evidence/
    ├── email_summary.csv
    └── slack_summary.json


Note:
For the demo, evidence files are summaries / sanitized, not raw messages.
This reinforces that the product is about scope and defensibility, not data dumping.

7. PDF outline (section-by-section, final)

This is the spine of the product.

1. Cover Page

“SEC Inquiry Response Pack”

Prepared for: [Fictional Firm Name]

Prepared on: [Date]

Review window

Pack ID (UUID)

2. Purpose and Context

One paragraph:

Why this pack was produced

Triggered by an SEC request

Built to document scope and response process

No sales language.
No claims of sufficiency.

3. Scope of Review

Bullet points:

Time window

Custodians

Systems reviewed

Source formats

Include a small table listing files ingested.

4. Explicit Exclusions

Clear bullets. No hedging.

This section is non-negotiable.

5. Summary of Observations

Tables only. No prose opinions.

Examples:

Message counts by custodian

Message counts by system

Category counts (as defined earlier)

6. Policy Context

List of policies reviewed (titles + effective dates)

Statement that categorization was aligned to definitions in those policies

No conclusions

7. Methodology and Reproducibility

Deterministic process

No modification of source content

Hash-based verification

Reference to manifest.json and verify.py

8. Closing Statement

One sentence:

“This Response Pack documents the scope, sources, and methodology used to support the firm’s response to the referenced SEC inquiry.”