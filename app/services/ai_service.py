"""
AI Service for OpenAI integration
Handles job description parsing and skill graph generation
"""
import os
import json
import logging
from typing import Dict, Any, Optional
import openai
from app.schemas.test_schema import SkillGraph, SkillNode
from app.core.config import settings

# Set OpenAI API key
os.environ["OPENAI_API_KEY"] = "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"

logger = logging.getLogger(__name__)

class AIService:
    """AI Service for OpenAI integration following Single Responsibility Principle"""
    
    def __init__(self):
        openai.api_key = os.environ["OPENAI_API_KEY"]
        self.model = "gpt-3.5-turbo"
    
    async def parse_job_description(self, job_description: str) -> Dict[str, Any]:
        """
        Parse job description using OpenAI
        Returns structured job data
        """
        try:
            prompt = f"""
            Parse the following job description and extract structured information:
            
            Job Description:
            {job_description}
            
            Return a JSON object with the following structure:
            {{
                "job_title": "extracted job title",
                "company": "company name if mentioned",
                "location": "job location",
                "job_type": "full-time/part-time/contract/remote",
                "experience_required": "experience level required",
                "key_responsibilities": ["responsibility 1", "responsibility 2"],
                "required_skills": ["skill 1", "skill 2", "skill 3"],
                "preferred_skills": ["skill 1", "skill 2"],
                "qualifications": ["qualification 1", "qualification 2"],
                "benefits": ["benefit 1", "benefit 2"],
                "salary_range": "salary range if mentioned",
                "summary": "brief summary of the role"
            }}
            
            Only return valid JSON, no additional text.
            """
            
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a expert HR assistant that parses job descriptions into structured data. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            parsed_data = json.loads(response.choices[0].message.content)
            logger.info(f"Successfully parsed job description")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing job description: {str(e)}")
            # Return default structure on error
            return {
                "job_title": "Unknown",
                "required_skills": [],
                "preferred_skills": [],
                "summary": "Error parsing job description",
                "error": str(e)
            }
    
    async def generate_skill_graph(self, parsed_job_description: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate skill graph from parsed job description
        Returns structured skill hierarchy
        """
        try:
            required_skills = parsed_job_description.get("required_skills", [])
            preferred_skills = parsed_job_description.get("preferred_skills", [])
            job_title = parsed_job_description.get("job_title", "")
            
            all_skills = required_skills + preferred_skills
            
            prompt = f"""
            Based on the job title "{job_title}" and these skills: {all_skills}, 
            create a hierarchical skill graph with priorities.
            
            Group related skills into categories and assign priorities:
            - H (High): Essential skills for the role
            - M (Medium): Important but not critical
            - L (Low): Nice to have
            
            Return JSON in this exact format:
            {{
                "root_nodes": [
                    {{
                        "skill": "Category Name (e.g., Programming Languages)",
                        "priority": "H",
                        "subskills": [
                            {{
                                "skill": "Specific Skill",
                                "priority": "H",
                                "subskills": []
                            }}
                        ]
                    }}
                ]
            }}
            
            Create logical groupings like:
            - Programming Languages
            - Frameworks & Libraries
            - Databases
            - Cloud Technologies
            - Tools & Methodologies
            - Soft Skills
            
            Only return valid JSON, no additional text.
            """
            
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert technical recruiter who creates skill hierarchies for job requirements. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=2000
            )
            
            skill_graph = json.loads(response.choices[0].message.content)
            logger.info(f"Successfully generated skill graph")
            return skill_graph
            
        except Exception as e:
            logger.error(f"Error generating skill graph: {str(e)}")
            # Return default structure on error
            return {
                "root_nodes": [
                    {
                        "skill": "General Skills",
                        "priority": "H",
                        "subskills": [
                            {
                                "skill": skill,
                                "priority": "M",
                                "subskills": []
                            } for skill in (parsed_job_description.get("required_skills", []))[:5]
                        ]
                    }
                ],
                "error": str(e)
            }
    
    async def process_job_description(self, job_description: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Complete AI processing pipeline
        Returns (parsed_job_description, skill_graph)
        """
        try:
            # Step 1: Parse job description
            parsed_jd = await self.parse_job_description(job_description)
            
            # Step 2: Generate skill graph
            skill_graph = await self.generate_skill_graph(parsed_jd)
            
            return parsed_jd, skill_graph
            
        except Exception as e:
            logger.error(f"Error in AI processing pipeline: {str(e)}")
            raise Exception(f"AI processing failed: {str(e)}")

# Singleton instance
ai_service = AIService()

def get_ai_service() -> AIService:
    """Dependency injection for AI service"""
    return ai_service
