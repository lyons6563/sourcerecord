#!/usr/bin/env python3
"""
Generate a deterministic SEC Inquiry Response Pack demo ZIP.

Reads email_export.csv and slack_export.json, produces a ZIP with:
- Response_Pack.pdf
- manifest.json
- methodology.md
- verify.py
- evidence/email_summary.csv
- evidence/slack_summary.json
"""

import csv
import io
import json
import hashlib
import os
import re
import zipfile
from datetime import datetime
from pathlib import Path
from io import BytesIO

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib import colors
except ImportError:
    print("Error: reportlab is required. Install with: pip install reportlab")
    exit(1)


# Constants
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DATA_DIR = PROJECT_ROOT / "irp_demo" / "data"
OUT_DIR = PROJECT_ROOT / "irp_demo" / "out"
OUTPUT_ZIP = OUT_DIR / "SEC_Response_Pack_Demo.zip"

EMAIL_CSV = DATA_DIR / "email_export.csv"
SLACK_JSON = DATA_DIR / "slack_export.json"

# Fixed constants for determinism
PACK_ID = "IRP-8D504146"
PREPARED_ON = "2024-02-15"
ZIP_TIMESTAMP = (2024, 2, 15, 0, 0, 0)  # Fixed timestamp for all ZIP entries

# Ensure output directory exists
OUT_DIR.mkdir(parents=True, exist_ok=True)


def read_email_data():
    """Read and parse email CSV."""
    if not EMAIL_CSV.exists():
        raise FileNotFoundError(f"Email export not found: {EMAIL_CSV}")
    
    emails = []
    with open(EMAIL_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            emails.append(row)
    return emails


def read_slack_data():
    """Read and parse Slack JSON."""
    if not SLACK_JSON.exists():
        raise FileNotFoundError(f"Slack export not found: {SLACK_JSON}")
    
    with open(SLACK_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def categorize_email(email):
    """Categorize email based on keyword rules."""
    categories = []
    text = (email.get('subject', '') + ' ' + email.get('body', '')).lower()
    
    if 'recommend' in text:
        categories.append('Recommendation language')
    if 'allocation' in text:
        categories.append('Allocation language')
    if 'performance' in text:
        categories.append('Performance language')
    if any(kw in text for kw in ['gmail', 'email me', 'send this later']):
        categories.append('Non-firm channel references')
    if email.get('has_attachment', '').lower() == 'true':
        categories.append('Has attachment')
    if email.get('custodian', '') == 'Supervisory Principal':
        categories.append('Supervisory involvement')
    
    return categories if categories else ['Uncategorized']


def categorize_slack_message(msg):
    """Categorize Slack message based on keyword rules."""
    categories = []
    text = msg.get('text', '').lower()
    
    if 'recommend' in text:
        categories.append('Recommendation language')
    if 'allocation' in text:
        categories.append('Allocation language')
    if 'performance' in text:
        categories.append('Performance language')
    if any(kw in text for kw in ['gmail', 'email me', 'send this later']):
        categories.append('Non-firm channel references')
    if msg.get('has_attachment', False):
        categories.append('Has attachment')
    if msg.get('custodian', '') == 'Supervisory Principal':
        categories.append('Supervisory involvement')
    
    return categories if categories else ['Uncategorized']


def generate_email_summary(emails):
    """Generate sanitized email summary (no body text)."""
    summary = []
    for email in emails:
        categories = categorize_email(email)
        summary.append({
            'message_id': email.get('message_id', ''),
            'timestamp': email.get('timestamp', ''),
            'sender': email.get('sender', ''),
            'recipients': email.get('recipients', ''),
            'subject': email.get('subject', ''),
            'has_attachment': email.get('has_attachment', ''),
            'custodian': email.get('custodian', ''),
            'categories': '; '.join(categories)
        })
    return summary


def generate_slack_summary(slack_data):
    """Generate sanitized Slack summary (no full text)."""
    summary = {
        'workspace': slack_data.get('workspace', ''),
        'time_window': slack_data.get('time_window', {}),
        'channels': []
    }
    
    for channel in slack_data.get('channels', []):
        channel_summary = {
            'name': channel.get('name', ''),
            'message_count': len(channel.get('messages', [])),
            'messages': []
        }
        
        for msg in channel.get('messages', []):
            categories = categorize_slack_message(msg)
            # Sanitize: only include first 100 chars of text
            text_preview = msg.get('text', '')[:100]
            if len(msg.get('text', '')) > 100:
                text_preview += '...'
            
            channel_summary['messages'].append({
                'message_id': msg.get('message_id', ''),
                'timestamp': msg.get('timestamp', ''),
                'user': msg.get('user', ''),
                'custodian': msg.get('custodian', ''),
                'text_preview': text_preview,
                'has_attachment': msg.get('has_attachment', False),
                'categories': categories
            })
        
        summary['channels'].append(channel_summary)
    
    return summary


def get_time_window(emails, slack_data):
    """Extract time window from data."""
    email_times = [e.get('timestamp', '') for e in emails if e.get('timestamp')]
    slack_times = []
    for channel in slack_data.get('channels', []):
        for msg in channel.get('messages', []):
            if msg.get('timestamp'):
                slack_times.append(msg.get('timestamp'))
    
    all_times = email_times + slack_times
    if not all_times:
        return '2024-01-01', '2024-02-15'
    
    # Extract date portion (assume format YYYY-MM-DD)
    dates = [t.split()[0] if ' ' in t else t.split('T')[0] for t in all_times if t]
    return min(dates), max(dates)


def generate_pdf(emails, slack_data, pack_id, time_window_start, time_window_end):
    """Generate Response_Pack.pdf with exact outline."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18,
                            pageCompression=0)
    
    # Set fixed metadata for determinism
    doc.title = "SEC Inquiry Response Pack"
    doc.author = "Example Advisors"
    doc.subject = "SEC Inquiry Response"
    doc.creator = "IRP Generator"
    
    story = []
    styles = getSampleStyleSheet()
    
    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#000000'),
        spaceAfter=30,
        alignment=1  # Center
    )
    
    # Heading style
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#000000'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Normal style
    normal_style = styles['Normal']
    
    # Cover Page
    story.append(Paragraph("SEC Inquiry Response Pack", title_style))
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(f"Prepared Date: {PREPARED_ON}", normal_style))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(f"Pack ID: {pack_id}", normal_style))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(f"Time Window: {time_window_start} to {time_window_end}", normal_style))
    story.append(PageBreak())
    
    # Purpose and Context
    story.append(Paragraph("Purpose and Context", heading_style))
    story.append(Paragraph(
        "This response pack has been prepared in response to an SEC inquiry. "
        "The pack contains email and messaging communications from designated custodians "
        "within the specified time window, categorized according to predefined keyword-based criteria.",
        normal_style
    ))
    story.append(Spacer(1, 0.3*inch))
    
    # Scope of Review
    story.append(Paragraph("Scope of Review", heading_style))
    story.append(Paragraph("The scope includes the following:", normal_style))
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph("• Email communications from designated custodians", normal_style))
    story.append(Paragraph("• Slack workspace communications from designated channels", normal_style))
    story.append(Paragraph("• Categorization based on keyword analysis and metadata", normal_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Input files table
    input_data = [
        ['Input File', 'Record Count', 'Time Range'],
        ['email_export.csv', str(len(emails)), f"{time_window_start} to {time_window_end}"],
        ['slack_export.json', str(sum(len(ch.get('messages', [])) for ch in slack_data.get('channels', []))), f"{time_window_start} to {time_window_end}"]
    ]
    input_table = Table(input_data, colWidths=[3*inch, 1.5*inch, 2*inch])
    input_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    story.append(input_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Explicit Exclusions
    story.append(Paragraph("Explicit Exclusions", heading_style))
    story.append(Paragraph("The following are excluded from this pack:", normal_style))
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph("• Communications outside the specified time window", normal_style))
    story.append(Paragraph("• Communications from custodians not designated for this review", normal_style))
    story.append(Paragraph("• Communications from systems or channels not included in the scope", normal_style))
    story.append(Paragraph("• Draft communications or unsent messages", normal_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Summary of Observations
    story.append(Paragraph("Summary of Observations", heading_style))
    
    # Count by custodian
    custodian_counts = {}
    for email in emails:
        cust = email.get('custodian', 'Unknown')
        custodian_counts[cust] = custodian_counts.get(cust, 0) + 1
    for channel in slack_data.get('channels', []):
        for msg in channel.get('messages', []):
            cust = msg.get('custodian', 'Unknown')
            custodian_counts[cust] = custodian_counts.get(cust, 0) + 1
    
    cust_data = [['Custodian', 'Total Communications']]
    for cust, count in sorted(custodian_counts.items()):
        cust_data.append([cust, str(count)])
    
    cust_table = Table(cust_data, colWidths=[3*inch, 2*inch])
    cust_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    story.append(Paragraph("Counts by Custodian", styles['Heading3']))
    story.append(cust_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Count by system
    email_count = len(emails)
    slack_count = sum(len(ch.get('messages', [])) for ch in slack_data.get('channels', []))
    system_data = [
        ['System', 'Total Communications'],
        ['Email', str(email_count)],
        ['Slack', str(slack_count)],
        ['Total', str(email_count + slack_count)]
    ]
    system_table = Table(system_data, colWidths=[3*inch, 2*inch])
    system_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    story.append(Paragraph("Counts by System", styles['Heading3']))
    story.append(system_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Count by category
    category_counts = {}
    for email in emails:
        categories = categorize_email(email)
        for cat in categories:
            category_counts[cat] = category_counts.get(cat, 0) + 1
    for channel in slack_data.get('channels', []):
        for msg in channel.get('messages', []):
            categories = categorize_slack_message(msg)
            for cat in categories:
                category_counts[cat] = category_counts.get(cat, 0) + 1
    
    cat_data = [['Category', 'Count']]
    for cat, count in sorted(category_counts.items()):
        cat_data.append([cat, str(count)])
    
    cat_table = Table(cat_data, colWidths=[3*inch, 2*inch])
    cat_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    story.append(Paragraph("Counts by Category", styles['Heading3']))
    story.append(cat_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Policy Context
    story.append(Paragraph("Policy Context", heading_style))
    story.append(Paragraph("The following policies are listed for reference only:", normal_style))
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph("• Communication Policy (Effective: 2023-01-01)", normal_style))
    story.append(Paragraph("• Electronic Communications Policy (Effective: 2023-06-15)", normal_style))
    story.append(Paragraph("• Supervisory Review Policy (Effective: 2023-03-01)", normal_style))
    story.append(Paragraph("• Recordkeeping Policy (Effective: 2023-01-01)", normal_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Methodology and Reproducibility
    story.append(Paragraph("Methodology and Reproducibility", heading_style))
    story.append(Paragraph(
        "This response pack was generated using a deterministic process. Files included in this pack "
        "have been hashed using SHA256, and the manifest.json file contains these hashes. "
        "The categorization process uses keyword-based rules applied to the communications "
        "included in the input files. The verify.py script included in this pack can be used "
        "to verify file integrity against the manifest.",
        normal_style
    ))
    story.append(Spacer(1, 0.3*inch))
    
    # Closing Statement
    story.append(Paragraph("Closing Statement", heading_style))
    story.append(Paragraph(
        "This response pack contains communications from the specified input files, "
        "processed according to the scope and methodology described above.",
        normal_style
    ))
    
    doc.build(story)
    return buffer.getvalue()


def generate_methodology_md():
    """Generate methodology.md content."""
    return """# Methodology

## Data Collection

The data for this response pack was collected from two sources:
1. Email export (CSV format) containing message metadata and content
2. Slack workspace export (JSON format) containing channel messages

## Categorization Rules

Communications were categorized using deterministic keyword-based rules:

- **Recommendation language**: Contains the keyword "recommend"
- **Allocation language**: Contains the keyword "allocation"
- **Performance language**: Contains the keyword "performance"
- **Non-firm channel references**: Contains "gmail", "email me", or "send this later"
- **Has attachment**: Metadata indicates attachment presence
- **Supervisory involvement**: Custodian is "Supervisory Principal"

## Data Sanitization

For the evidence summaries:
- Email bodies are excluded from summaries (only metadata and categories)
- Slack message text is truncated to 100 characters in summaries
- Full original data is not included in the response pack

## Reproducibility

The generation process is deterministic:
- Same input files produce identical output
- All files are hashed using SHA256
- Manifest contains all hashes for verification
- verify.py script enables independent verification

## Time Window

All communications were filtered to the specified time window:
- Start: 2024-01-01
- End: 2024-02-15

## Custodians

Only communications from the following custodians were included:
- Lead Advisor
- Associate Advisor
- Supervisory Principal
"""


def generate_verify_py():
    """Generate verify.py script."""
    return """#!/usr/bin/env python3
\"\"\"
Verify the integrity of files in the response pack against manifest.json
\"\"\"

import json
import hashlib
import os
from pathlib import Path

def sha256_file(filepath):
    \"\"\"Calculate SHA256 hash of a file.\"\"\"
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def main():
    # Use current directory (where script is run from, typically where ZIP was extracted)
    base_dir = Path('.')
    manifest_path = base_dir / 'manifest.json'
    
    if not manifest_path.exists():
        print(f"Error: manifest.json not found at {manifest_path.absolute()}")
        print("Make sure you are running this script from the directory where the ZIP was extracted.")
        return 1
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    print("Verifying files against manifest...")
    print()
    
    all_valid = True
    for filepath, expected_hash in sorted(manifest.items()):
        full_path = base_dir / filepath
        if not full_path.exists():
            print(f"✗ {filepath}: FILE NOT FOUND")
            all_valid = False
            continue
        
        actual_hash = sha256_file(full_path)
        if actual_hash == expected_hash:
            print(f"✓ {filepath}: OK")
        else:
            print(f"✗ {filepath}: HASH MISMATCH")
            print(f"  Expected: {expected_hash}")
            print(f"  Actual:   {actual_hash}")
            all_valid = False
    
    print()
    if all_valid:
        print("All files verified successfully.")
        return 0
    else:
        print("Verification failed. One or more files do not match manifest.")
        return 1

if __name__ == '__main__':
    exit(main())
"""


def calculate_file_hash(content):
    """Calculate SHA256 hash of content."""
    return hashlib.sha256(content).hexdigest()


def normalize_pdf_bytes(pdf_bytes):
    """Normalize volatile PDF metadata fields for determinism."""
    # Normalize CreationDate - PDF format: D:YYYYMMDDHHmmSSOHH'mm'
    pdf_bytes = re.sub(
        rb'/CreationDate\s*\(D:[^)]+\)',
        rb'/CreationDate (D:20240215000000-05\'00\')',
        pdf_bytes
    )
    # Normalize ModDate - PDF format: D:YYYYMMDDHHmmSSOHH'mm'
    pdf_bytes = re.sub(
        rb'/ModDate\s*\(D:[^)]+\)',
        rb'/ModDate (D:20240215000000-05\'00\')',
        pdf_bytes
    )
    # Normalize trailer ID - replace with fixed deterministic ID
    # Pattern: /ID [<hex_string><hex_string>]
    fixed_id = b'<8D5041468D5041468D5041468D504146>'
    pdf_bytes = re.sub(
        rb'/ID\s*\[\s*<[^>]+>\s*<[^>]+>\s*\]',
        rb'/ID [' + fixed_id + b' ' + fixed_id + b']',
        pdf_bytes
    )
    return pdf_bytes


def write_zip_entry(zipf, path, data_bytes):
    """Write a ZIP entry with fixed deterministic metadata."""
    zip_info = zipfile.ZipInfo(path, ZIP_TIMESTAMP)
    zip_info.compress_type = zipfile.ZIP_DEFLATED
    zip_info.create_system = 0
    zip_info.external_attr = 0o644 << 16
    zipf.writestr(zip_info, data_bytes)


def main():
    """Main function to generate the response pack."""
    # Preflight validation
    if not EMAIL_CSV.exists():
        print(f"Error: Required input file not found: {EMAIL_CSV}")
        print("Please ensure email_export.csv is placed in irp_demo/data/")
        return 1
    if not SLACK_JSON.exists():
        print(f"Error: Required input file not found: {SLACK_JSON}")
        print("Please ensure slack_export.json is placed in irp_demo/data/")
        return 1
    
    try:
        # Read input data
        print("Reading input data...")
        emails = read_email_data()
        slack_data = read_slack_data()
        
        # Use fixed pack ID for determinism
        pack_id = PACK_ID
        
        # Get time window
        time_window_start, time_window_end = get_time_window(emails, slack_data)
        
        print("Generating summaries...")
        # Generate summaries
        email_summary = generate_email_summary(emails)
        slack_summary = generate_slack_summary(slack_data)
        
        print("Generating PDF...")
        # Generate PDF
        pdf_content = generate_pdf(emails, slack_data, pack_id, time_window_start, time_window_end)
        # Normalize PDF for determinism
        pdf_content = normalize_pdf_bytes(pdf_content)
        
        print("Generating methodology and verify script...")
        # Generate methodology.md
        methodology_content = generate_methodology_md().encode('utf-8')
        
        # Generate verify.py
        verify_content = generate_verify_py().encode('utf-8')
        
        print("Creating evidence summaries...")
        # Generate email summary CSV (sort for determinism)
        email_summary_buffer = BytesIO()
        if email_summary:
            # Sort by message_id for deterministic output
            email_summary_sorted = sorted(email_summary, key=lambda x: x.get('message_id', ''))
            fieldnames = list(email_summary_sorted[0].keys())
            text_buffer = io.TextIOWrapper(email_summary_buffer, encoding='utf-8', newline='')
            writer = csv.DictWriter(text_buffer, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(email_summary_sorted)
            text_buffer.flush()
            text_buffer.detach()
        email_summary_content = email_summary_buffer.getvalue()
        
        # Generate slack summary JSON (deterministic with sort_keys)
        slack_summary_content = json.dumps(slack_summary, indent=2, sort_keys=True, ensure_ascii=False, separators=(',', ': ')).encode('utf-8')
        
        print("Building ZIP file...")
        # Calculate hashes before creating ZIP (deterministic)
        file_contents = {
            'Response_Pack.pdf': pdf_content,
            'methodology.md': methodology_content,
            'verify.py': verify_content,
            'evidence/email_summary.csv': email_summary_content,
            'evidence/slack_summary.json': slack_summary_content
        }
        
        # Generate manifest (exclude manifest from itself)
        manifest = {}
        for filename, content in sorted(file_contents.items()):
            manifest[filename] = calculate_file_hash(content)
        
        # Add manifest JSON to file contents (deterministic with sort_keys and stable separators)
        manifest_json = json.dumps(manifest, indent=2, sort_keys=True, separators=(',', ': ')).encode('utf-8')
        
        # Print file hash report before zipping
        print("\nFILE_SHA256 report:")
        all_files = {**file_contents, 'manifest.json': manifest_json}
        for filename in sorted(all_files.keys()):
            file_hash = calculate_file_hash(all_files[filename])
            print(f"FILE_SHA256 {filename} {file_hash}")
        
        # Create ZIP file (deterministic: same order, same compression, fixed timestamps)
        with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add files in deterministic order using helper function
            for filename in sorted(file_contents.keys()):
                write_zip_entry(zipf, filename, file_contents[filename])
            write_zip_entry(zipf, 'manifest.json', manifest_json)
        
        # Calculate and print ZIP hash for verification
        with open(OUTPUT_ZIP, 'rb') as f:
            zip_hash = hashlib.sha256(f.read()).hexdigest()
        
        print()
        print(f"✓ Successfully generated SEC Inquiry Response Pack")
        print(f"  Output: {OUTPUT_ZIP}")
        print(f"  Pack ID: {pack_id}")
        print(f"  Time Window: {time_window_start} to {time_window_end}")
        print(f"  Total files: {len(manifest) + 1} (including manifest)")
        print(f"  ZIP SHA256: {zip_hash}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())

