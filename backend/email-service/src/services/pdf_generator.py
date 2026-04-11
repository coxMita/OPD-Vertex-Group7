"""PDF generation for email attachments."""

from typing import Any

from fpdf import FPDF


def generate_pdf(title: str, content: str | dict[str, Any]) -> bytes:
    """Generate a simple PDF from text or a dictionary of data.

    Returns:
        The PDF file as bytes.

    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", style="B", size=16)

    pdf.cell(0, 10, title, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    pdf.set_font("Helvetica", size=12)

    if isinstance(content, dict):
        for key, value in content.items():
            pdf.set_font("Helvetica", style="B", size=12)
            pdf.cell(0, 8, f"{key.title()}:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", size=12)
            pdf.multi_cell(0, 8, str(value), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(4)
    else:
        pdf.multi_cell(0, 8, str(content), new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())
