import json
import logging
from typing import Dict, List
from utils.openai_client import get_openai_client
from utils.scoring_engine import ScoringEngine

logger = logging.getLogger(__name__)


class ResumeAnalyzer:
    """Main orchestrator for resume analysis"""
    
    def __init__(self):
        self.client = get_openai_client()
        self.scoring_engine = ScoringEngine()
    
    def extract_overlapping_skills(self, resume_text: str, job_description: str) -> List[str]:
        """
        Identify skills that appear in both resume and job description
        
        Returns:
            List of overlapping skills
        """
        system_prompt = """You are an expert at analyzing resumes and job descriptions.
Identify all skills, technologies, tools, qualifications, and competencies that appear in BOTH the resume and job description.

Consider:
- Technical skills (programming languages, frameworks, tools)
- Soft skills (leadership, communication, etc.)
- Domain knowledge
- Certifications and qualifications
- Methodologies (Agile, Scrum, etc.)

Return ONLY a JSON array of strings, each representing an overlapping skill.
Example: ["Python", "Project Management", "AWS", "Team Leadership"]"""
        
        user_prompt = f"""Job Description:
{job_description}

---

Resume:
{resume_text}

---

List all overlapping skills as a JSON array."""
        
        try:
            response = self.client.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            # Parse response - handle both array and object formats
            parsed = json.loads(response)
            if isinstance(parsed, list):
                skills = parsed
            elif isinstance(parsed, dict) and "skills" in parsed:
                skills = parsed["skills"]
            elif isinstance(parsed, dict) and "overlapping_skills" in parsed:
                skills = parsed["overlapping_skills"]
            else:
                # Try to find any array in the response
                for value in parsed.values():
                    if isinstance(value, list):
                        skills = value
                        break
                else:
                    skills = []
            
            logger.info(f"Found {len(skills)} overlapping skills")
            return skills
        
        except Exception as e:
            logger.error(f"Failed to extract overlapping skills: {e}")
            return []
    
    def identify_skill_gaps(self, resume_text: str, job_description: str) -> List[Dict]:
        """
        Identify skills mentioned in job description but missing or weak in resume
        
        Returns:
            List of dicts with 'skill', 'importance' (high/medium/low), and 'suggestion'
        """
        system_prompt = """You are an expert at analyzing skill gaps between resumes and job requirements.
Identify skills, qualifications, or experience mentioned in the job description that are:
1. Completely missing from the resume
2. Mentioned but appear weak or underdeveloped in the resume

For each gap, assess its importance level (high/medium/low) based on how critical it seems to the role.
Provide a brief suggestion on how to address the gap.

Return your response as valid JSON with this structure:
{
    "gaps": [
        {
            "skill": "<skill name>",
            "importance": "<high|medium|low>",
            "suggestion": "<brief actionable suggestion>"
        }
    ]
}"""
        
        user_prompt = f"""Job Description:
{job_description}

---

Resume:
{resume_text}

---

Identify all skill gaps."""
        
        try:
            response = self.client.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response)
            gaps = result.get("gaps", [])
            
            logger.info(f"Identified {len(gaps)} skill gaps")
            return gaps
        
        except Exception as e:
            logger.error(f"Failed to identify skill gaps: {e}")
            return []
    
    def generate_executive_summary(self, resume_text: str, job_description: str, 
                                   overall_score: float, overlapping_skills: List[str],
                                   skill_gaps: List[Dict]) -> str:
        """
        Generate an executive summary of the analysis
        
        Returns:
            Executive summary text
        """
        system_prompt = """You are an expert career advisor. Create a concise executive summary 
(2-3 sentences) that captures the key findings of this resume analysis.

Focus on:
- Overall fit for the role
- Key strengths
- Most critical areas for improvement

Be encouraging but honest."""
        
        user_prompt = f"""Overall Fit Score: {overall_score}/100
Number of Overlapping Skills: {len(overlapping_skills)}
Number of Skill Gaps: {len(skill_gaps)}
High-Priority Gaps: {len([g for g in skill_gaps if g.get('importance') == 'high'])}

Job Description:
{job_description[:500]}...

Resume:
{resume_text[:500]}...

Write an executive summary."""
        
        try:
            response = self.client.structured_completion(system_prompt, user_prompt)
            return response.strip()
        
        except Exception as e:
            logger.error(f"Failed to generate executive summary: {e}")
            return f"This resume shows a {overall_score}% fit for the target role based on our analysis."
    
    def analyze_resume(self, resume_text: str, job_description: str) -> Dict:
        """
        Perform complete resume analysis
        
        Returns:
            Comprehensive analysis results
        """
        logger.info("Starting comprehensive resume analysis")
        
        # Extract overlapping skills
        logger.info("Step 1: Extracting overlapping skills")
        overlapping_skills = self.extract_overlapping_skills(resume_text, job_description)
        
        # Identify skill gaps
        logger.info("Step 2: Identifying skill gaps")
        skill_gaps = self.identify_skill_gaps(resume_text, job_description)
        
        # Evaluate all dimensions
        logger.info("Step 3: Evaluating dimensions")
        dimension_results = self.scoring_engine.evaluate_all_dimensions(resume_text, job_description)
        
        # Generate overall recommendations
        logger.info("Step 4: Generating recommendations")
        overall_recommendations = self.scoring_engine.generate_overall_recommendations(dimension_results)
        
        # Generate executive summary
        logger.info("Step 5: Generating executive summary")
        executive_summary = self.generate_executive_summary(
            resume_text, job_description, dimension_results["overall_score"],
            overlapping_skills, skill_gaps
        )
        
        # Compile complete analysis
        analysis = {
            "overall_score": dimension_results["overall_score"],
            "executive_summary": executive_summary,
            "overlapping_skills": overlapping_skills,
            "skill_gaps": skill_gaps,
            "dimensions": {
                dim: dimension_results[dim]
                for dim in ScoringEngine.DIMENSIONS
            },
            "dimension_weights": dimension_results["dimension_weights"],
            "overall_recommendations": overall_recommendations
        }
        
        logger.info(f"Analysis complete. Overall score: {analysis['overall_score']}")
        return analysis

