import os
import re
from datetime import datetime
from tempfile import mkdtemp

from fpdf import FPDF

from remarkdav.sync_db import File


def clean_string(s: str) -> str:
    """Remove all non latin-1 characters."""
    return re.sub(r"[^\x00-\x7F\x80-\xFF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]", "", s)


def create_sync_status_pdf(mapping: dict) -> str:
    # Get all synced filess
    qs = File.select().where(File.source == mapping["id"], File.uploaded == True)  # noqa

    # Create PDF
    pdf = FPDF()
    pdf.add_page()

    # Add title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(40, 10, "Sync status", ln=1)

    # Add sync date and time
    pdf.set_font("Arial", size=12)
    pdf.cell(40, 20, f"Date and time: {datetime.now()}", ln=1)

    for file in qs:
        # Add rows with files
        pdf.cell(200, 8, clean_string(file.upload_path), ln=1)
        pdf.cell(50, 10, "", ln=0)
        pdf.cell(50, 10, str(file.modified), ln=1)

    filename = os.path.join(mkdtemp(), "status.pdf")
    pdf.output(filename, "F")

    return filename
