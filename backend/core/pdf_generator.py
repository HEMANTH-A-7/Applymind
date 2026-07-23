"""
Resume PDF Generator — ReportLab
Converts ATS-rewritten resume text into a professional, ATS-safe PDF.
No images, tables, columns, or special characters.
"""
import re
from pathlib import Path
from datetime import datetime
from loguru import logger

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("ReportLab not installed. PDF generation disabled. Run: pip install reportlab")


OUTPUT_DIR = Path("generated_resumes")
OUTPUT_DIR.mkdir(exist_ok=True)


def _sanitize(text: str) -> str:
    """Remove characters that break ReportLab XML parser."""
    replacements = {
        "&": "&amp;", "<": "&lt;", ">": "&gt;",
        "\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "--", "\u2022": "-",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def _sanitize_contact(text: str) -> str:
    """Sanitize the contact line while turning "[Label](url)" markdown into a clickable
    ReportLab link — lets LinkedIn/GitHub/Portfolio render as short blue link text instead
    of raw URLs, matching the candidate's actual resume style."""
    parts = []
    last = 0
    for m in _LINK_RE.finditer(text):
        parts.append(_sanitize(text[last:m.start()]))
        label, url = m.group(1), m.group(2).replace('"', "%22")
        parts.append(f'<link href="{url}" color="#1a56db"><u>{_sanitize(label)}</u></link>')
        last = m.end()
    parts.append(_sanitize(text[last:]))
    return "".join(parts)


def generate_pdf_from_text(
    resume_text: str,
    candidate_name: str = "Candidate",
    job_title: str = "",
    company: str = "",
    output_filename: str = None,
) -> str:
    """
    Generate an ATS-safe PDF from plain resume text.

    Args:
        resume_text: Full resume as plain text (from Agent 05 output)
        candidate_name: Used for filename
        job_title: Used for filename
        company: Used for filename
        output_filename: Optional override for output path

    Returns:
        Absolute path to generated PDF
    """
    if not REPORTLAB_AVAILABLE:
        raise ImportError("ReportLab not installed. Run: pip install reportlab")

    safe_name = candidate_name.replace(" ", "_")
    safe_company = company.replace(" ", "_")[:20] if company else "application"
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
    filename = output_filename or str(OUTPUT_DIR / f"{safe_name}_{safe_company}_{timestamp}.pdf")

    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    # ─── Styles (ATS-safe: Calibri/Times equivalents, no fancy fonts) ───
    styles = getSampleStyleSheet()

    name_style = ParagraphStyle(
        "Name",
        fontName="Times-Bold",
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=4,
        textColor=colors.black,
    )
    contact_style = ParagraphStyle(
        "Contact",
        fontName="Times-Roman",
        fontSize=10,
        alignment=TA_CENTER,
        spaceAfter=8,
        textColor=colors.black,
    )
    section_header_style = ParagraphStyle(
        "SectionHeader",
        fontName="Times-Bold",
        fontSize=11,
        spaceBefore=10,
        spaceAfter=4,
        textColor=colors.black,
        borderPadding=(0, 0, 2, 0),
    )
    body_style = ParagraphStyle(
        "Body",
        fontName="Times-Roman",
        fontSize=10,
        leading=14,
        spaceAfter=3,
        textColor=colors.black,
    )
    bullet_style = ParagraphStyle(
        "Bullet",
        fontName="Times-Roman",
        fontSize=10,
        leading=14,
        leftIndent=15,
        spaceAfter=2,
        textColor=colors.black,
        bulletText="-",
        bulletFontName="Times-Roman",
        bulletFontSize=10,
        bulletIndent=5,
    )

    content = []
    lines = resume_text.strip().split("\n")

    # Parse sections from plain text
    current_section = None
    in_experience = False

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        clean = _sanitize(line)

        # Detect name (first non-empty line)
        if i == 0 or (i < 3 and not any(kw in line.upper() for kw in ["SUMMARY", "SKILLS", "EXPERIENCE", "EDUCATION", "PROJECT"])):
            if i == 0:
                content.append(Paragraph(clean, name_style))
                continue

        # Contact info (email/phone patterns)
        if i < 5 and ("@" in line or line.startswith("+") or "|" in line):
            content.append(Paragraph(_sanitize_contact(line), contact_style))
            continue

        # Section headers (ALL CAPS lines or known section names)
        section_keywords = ["SUMMARY", "SKILLS", "TECHNICAL", "EXPERIENCE", "EDUCATION", "PROJECTS", "CERTIFICATIONS", "ACHIEVEMENTS", "AWARDS"]
        if any(kw in line.upper() for kw in section_keywords) and len(line) < 40:
            content.append(Spacer(1, 4))
            content.append(Paragraph(clean.upper(), section_header_style))
            content.append(HRFlowable(width="100%", thickness=0.5, color=colors.black))
            current_section = line.upper()
            continue

        # Bullet points
        if line.startswith(("-", "•", "*", "·")):
            bullet_text = _sanitize(line[1:].strip())
            content.append(Paragraph(f"- {bullet_text}", bullet_style))
            continue

        # Regular body text
        content.append(Paragraph(clean, body_style))

    try:
        doc.build(content)
        logger.success(f"[PDF Generator] Created: {filename}")
        return filename
    except Exception as e:
        logger.error(f"[PDF Generator] Failed: {e}")
        raise


def generate_pdf_from_parsed_resume(parsed_resume: dict, output_filename: str = None) -> str:
    """
    Generate PDF directly from the parsed resume JSON (Agent 01 output).
    Formats it into proper resume sections.
    """
    contact = parsed_resume.get("contact", {})
    name = contact.get("name", "Candidate")

    lines = []

    # Header
    lines.append(name)
    contact_parts = filter(None, [
        contact.get("email", ""),
        contact.get("phone", ""),
        contact.get("location", ""),
        contact.get("linkedin", ""),
    ])
    lines.append(" | ".join(contact_parts))
    lines.append("")

    # Summary
    if parsed_resume.get("summary"):
        lines.append("PROFESSIONAL SUMMARY")
        lines.append(parsed_resume["summary"])
        lines.append("")

    # Skills
    skills = parsed_resume.get("skills", {})
    if skills:
        lines.append("TECHNICAL SKILLS")
        all_skills = skills.get("technical", []) + skills.get("tools", [])
        lines.append(", ".join(all_skills))
        lines.append("")

    # Experience
    if parsed_resume.get("experience"):
        lines.append("PROFESSIONAL EXPERIENCE")
        for exp in parsed_resume["experience"]:
            lines.append(f"{exp.get('role', '')} | {exp.get('company', '')} | {exp.get('start_date', '')} - {exp.get('end_date', 'Present')}")
            for bullet in exp.get("bullets", []):
                lines.append(f"- {bullet}")
            lines.append("")

    # Projects
    if parsed_resume.get("projects"):
        lines.append("PROJECTS")
        for proj in parsed_resume["projects"]:
            lines.append(f"{proj.get('name', '')} | {', '.join(proj.get('tech_stack', []))}")
            for bullet in proj.get("bullets", []):
                lines.append(f"- {bullet}")
            lines.append("")

    # Education
    if parsed_resume.get("education"):
        lines.append("EDUCATION")
        for edu in parsed_resume["education"]:
            lines.append(f"{edu.get('degree', '')} | {edu.get('institution', '')} | {edu.get('year', '')}")
            lines.append("")

    # Certifications
    if parsed_resume.get("certifications"):
        lines.append("CERTIFICATIONS")
        for cert in parsed_resume["certifications"]:
            lines.append(f"- {cert}")

    resume_text = "\n".join(lines)
    return generate_pdf_from_text(resume_text, name, output_filename=output_filename)
