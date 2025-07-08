import os
import json
import re
from typing import Dict, Any, Optional
from datetime import datetime

try:
    from PyPDF2 import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import openai
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

class AIScreeningService:
    """Service for AI-powered resume screening and job matching using notebook logic"""
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.ai_enabled = bool(self.api_key and self.api_key != "your-openai-api-key-here" and AI_AVAILABLE)
        if self.ai_enabled:
            openai.api_key = self.api_key

    def extract_text_from_file(self, file_path: str) -> str:
        if not file_path or not os.path.exists(file_path):
            return "Error: File path is invalid or file does not exist"
        try:
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.pdf' and PDFPLUMBER_AVAILABLE:
                with pdfplumber.open(file_path) as pdf:
                    text = "\n".join(page.extract_text() or "" for page in pdf.pages)
                return text.strip() or "No text extracted from PDF"
            elif ext in ['.docx', '.doc'] and DOCX_AVAILABLE:
                doc = Document(file_path)
                text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
                return text.strip() or "No text extracted from DOCX file"
            else:
                return f"Unsupported file type: {ext}"
        except Exception as e:
            return f"Error extracting text: {e}"

    def screen_resume_text(self, resume_text: str, job_description: str, parsed_job_description: Optional[str] = None, skill_graph: Optional[str] = None, min_resume_score: Optional[int] = None) -> Dict[str, Any]:
        jd_context = job_description
        if parsed_job_description:
            jd_context += f"\n\nStructured JD Info:\n{parsed_job_description}"
        if skill_graph:
            jd_context += f"\n\nSkill Graph:\n{skill_graph}"
        prompt = f"""
You are an AI assistant helping recruiters evaluate resumes.
Given the following job description and candidate resume, analyze and return a JSON object with:
- resume_score (0–100)
- skill_match_percentage
- experience_score (0–100)
- education_score (0–100)
- ai_reasoning (1–2 sentence explanation)
Job Description:
{jd_context}
Resume:
{resume_text}
"""
        if not self.ai_enabled:
            return self._screen_resume_mock(resume_text, job_description)
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            result_json = json.loads(response.choices[0].message.content)
        except Exception as e:
            return {
                "resume_score": 0,
                "skill_match_percentage": 0,
                "experience_score": 0,
                "education_score": 0,
                "ai_reasoning": f"AI error: {e}",
                "is_shortlisted": False
            }
        is_shortlisted = False
        if min_resume_score is not None:
            try:
                if float(result_json.get("resume_score", 0)) >= min_resume_score:
                    is_shortlisted = True
            except Exception:
                pass
        result_json["is_shortlisted"] = is_shortlisted
        result_json["parsed_resume"] = self._parse_resume_basic(resume_text)
        return result_json

    def _screen_resume_mock(self, resume_text: str, job_description: str) -> Dict[str, Any]:
        resume_lower = resume_text.lower()
        jd_lower = job_description.lower()
        skills = ['python', 'java', 'javascript', 'react', 'angular', 'vue', 'node.js',
                 'django', 'flask', 'spring', 'sql', 'postgresql', 'mysql', 'mongodb',
                 'aws', 'azure', 'docker', 'kubernetes', 'git', 'fastapi']
        skill_matches = sum(1 for skill in skills if skill in resume_lower and skill in jd_lower)
        total_skills = sum(1 for skill in skills if skill in jd_lower)
        skill_percentage = (skill_matches / max(total_skills, 1)) * 100
        experience_matches = re.findall(r'(\d+)[\+\s]*year', resume_lower)
        years_experience = max([int(year) for year in experience_matches] + [0])
        base_score = min(skill_percentage, 100)
        experience_bonus = min(years_experience * 5, 20)
        final_score = min(int(base_score + experience_bonus), 100)
        reasoning = f"Mock AI Analysis: Found {skill_matches}/{total_skills} skill matches, "
        reasoning += f"{years_experience} years experience. "
        if final_score >= 80:
            reasoning += "Strong match for the position."
        elif final_score >= 60:
            reasoning += "Good match with some gaps."
        elif final_score >= 40:
            reasoning += "Moderate match, needs development."
        else:
            reasoning += "Limited match for this position."
        return {
            'resume_score': final_score,
            'skill_match_percentage': skill_percentage,
            'experience_score': min(years_experience * 10, 100),
            'education_score': 75,
            'ai_reasoning': reasoning,
            'parsed_resume': self._parse_resume_basic(resume_text),
            'is_shortlisted': final_score >= 70
        }

    def _parse_resume_basic(self, resume_text: str) -> Dict[str, Any]:
        return {
            "raw_text": resume_text,
            "parsed_at": datetime.now().isoformat()
        }
