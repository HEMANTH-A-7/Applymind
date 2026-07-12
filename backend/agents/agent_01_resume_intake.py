"""
Agent 01 — Resume Intake Agent
Parses uploaded PDF/DOCX resumes into a structured JSON schema.
"""
from pathlib import Path
from typing import Optional
from loguru import logger

from core.groq_llm import chat_json, GroqNotConfiguredError


PARSE_PROMPT = """You are a resume parser. Extract all structured information from this resume text and return ONLY valid JSON.

Output format:
{
  "contact": {
    "name": "",
    "email": "",
    "phone": "",
    "location": "",
    "linkedin": "",
    "github": "",
    "portfolio": ""
  },
  "summary": "",
  "skills": {
    "technical": [],
    "soft": [],
    "tools": [],
    "languages": []
  },
  "experience": [
    {
      "role": "",
      "company": "",
      "location": "",
      "start_date": "",
      "end_date": "",
      "current": false,
      "bullets": [],
      "metrics": []
    }
  ],
  "education": [
    {
      "degree": "",
      "institution": "",
      "year": "",
      "gpa": "",
      "coursework": []
    }
  ],
  "projects": [
    {
      "name": "",
      "description": "",
      "tech_stack": [],
      "url": "",
      "bullets": []
    }
  ],
  "certifications": [],
  "awards": [],
  "ats_issues": [],
  "total_experience_years": 0
}

Resume text:
{resume_text}

Return ONLY the JSON, no explanations."""


ATS_CHECK_PROMPT = """Analyze this resume for ATS compliance issues and return a JSON list of issues found.

Issues to check:
- Missing quantified metrics in bullet points
- No summary/objective section
- Missing skills section
- Tables or columns detected (bad for ATS)
- Special characters or symbols
- Generic job titles
- Missing dates
- Too short (<400 words) or too long (>1000 words)
- No measurable impact in bullets

Return format: ["issue 1", "issue 2", ...]

Resume text:
{resume_text}

Return ONLY the JSON array."""


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF using pdfplumber or pypdf."""
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except ImportError:
        pass
    try:
        import pypdf
        reader = pypdf.PdfReader(file_path)
        return "\n".join(page.extract_text() for page in reader.pages)
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return ""


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX using python-docx."""
    try:
        from docx import Document
        doc = Document(file_path)
        return "\n".join(para.text for para in doc.paragraphs)
    except Exception as e:
        logger.error(f"DOCX extraction failed: {e}")
        return ""


def extract_raw_text(file_path: str) -> str:
    """Route to correct extractor based on file extension."""
    path = Path(file_path)
    ext = path.suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext in [".docx", ".doc"]:
        return extract_text_from_docx(file_path)
    elif ext == ".txt":
        return path.read_text(encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def parse_resume_with_groq(raw_text: str) -> dict:
    """Use Groq LLM to parse resume text into structured JSON. Raises on failure."""
    result = chat_json(
        messages=[{"role": "user", "content": PARSE_PROMPT.replace("{resume_text}", raw_text[:8000])}],
        temperature=0.1,
        max_tokens=6000,
    )
    if not isinstance(result, dict):
        raise ValueError("Resume parser returned non-object JSON")
    return result


def check_ats_compliance(raw_text: str) -> list:
    """Identify ATS compliance issues in the resume. Fails open (empty list)."""
    try:
        result = chat_json(
            messages=[{"role": "user", "content": ATS_CHECK_PROMPT.replace("{resume_text}", raw_text[:4000])}],
            temperature=0.1,
            max_tokens=800,
            json_mode=False,  # prompt asks for a bare JSON array
        )
        return result if isinstance(result, list) else []
    except Exception as e:
        logger.error(f"ATS check failed: {e}")
        return []


def run(file_path: str, user_id: Optional[str] = None) -> dict:
    """
    Main entry point for Agent 01 — Resume Intake Agent.
    
    Args:
        file_path: Absolute path to uploaded resume (PDF/DOCX/TXT)
        user_id: Optional user ID for logging
    
    Returns:
        dict with keys: raw_text, parsed_data, ats_issues, status
    """
    logger.info(f"[Agent 01] Parsing resume: {file_path}")
    
    try:
        raw_text = extract_raw_text(file_path)
        if not raw_text.strip():
            return {"status": "error", "message": "Could not extract text from resume"}

        try:
            parsed_data = parse_resume_with_groq(raw_text)
        except GroqNotConfiguredError as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            logger.error(f"[Agent 01] Resume parsing failed: {e}")
            return {"status": "error", "message": f"Resume parsing failed: {e}"}

        ats_issues = check_ats_compliance(raw_text)
        
        # Merge ATS issues back into parsed data
        parsed_data["ats_issues"] = ats_issues
        
        # Build skills taxonomy
        all_skills = (
            parsed_data.get("skills", {}).get("technical", []) +
            parsed_data.get("skills", {}).get("tools", [])
        )
        parsed_data["skills_flat"] = list(set(s.lower() for s in all_skills))
        
        logger.success(f"[Agent 01] Resume parsed: {len(all_skills)} skills, {len(ats_issues)} ATS issues")
        
        return {
            "status": "success",
            "raw_text": raw_text,
            "parsed_data": parsed_data,
            "ats_issues": ats_issues,
            "word_count": len(raw_text.split()),
        }
    
    except Exception as e:
        logger.error(f"[Agent 01] Failed: {e}")
        return {"status": "error", "message": str(e)}
