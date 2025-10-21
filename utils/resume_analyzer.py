import json
from typing import Dict, List
import time

# Import centralized logging
from utils.logging_config import get_logger

from utils.openai_client import get_openai_client
from utils.scoring_engine import ScoringEngine

logger = get_logger(__name__)


class ResumeAnalyzer:
    """Main orchestrator for resume analysis"""
    
    def __init__(self):
        logger.info("Initializing ResumeAnalyzer")
        self.client = get_openai_client()
        self.scoring_engine = ScoringEngine()
        logger.info("✓ ResumeAnalyzer initialized with OpenAI client and scoring engine")
    
    def extract_overlapping_skills(self, resume_text: str, job_description: str) -> List[str]:
        """
        Identify skills that appear in both resume and job description
        
        Returns:
            List of overlapping skills
        """
        logger.info("=" * 80)
        logger.info("🔍 EXTRACTING OVERLAPPING SKILLS")
        logger.info("=" * 80)
        logger.debug(f"Resume length: {len(resume_text)} characters")
        logger.debug(f"Job description length: {len(job_description)} characters")
        
        start_time = time.time()
        
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
        
        logger.debug("Sending skill extraction request to OpenAI")
        
        try:
            response = self.client.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                operation="extract_overlapping_skills"
            )
            
            logger.debug(f"OpenAI response received (length: {len(response)} chars)")
            logger.debug(f"Response preview: {response[:200]}...")
            
            # Parse response - handle both array and object formats
            parsed = json.loads(response)
            logger.debug(f"Parsed response type: {type(parsed)}")
            
            if isinstance(parsed, list):
                skills = parsed
                logger.debug("Response is a direct list")
            elif isinstance(parsed, dict) and "skills" in parsed:
                skills = parsed["skills"]
                logger.debug("Extracted skills from 'skills' key")
            elif isinstance(parsed, dict) and "overlapping_skills" in parsed:
                skills = parsed["overlapping_skills"]
                logger.debug("Extracted skills from 'overlapping_skills' key")
            else:
                # Try to find any array in the response
                logger.debug("Searching for array in response values")
                for key, value in parsed.items():
                    if isinstance(value, list):
                        skills = value
                        logger.debug(f"Found skills list in key: {key}")
                        break
                else:
                    skills = []
                    logger.warning("No skills list found in response")
            
            duration = time.time() - start_time
            logger.info("=" * 80)
            logger.info(f"✅ OVERLAPPING SKILLS EXTRACTION COMPLETE")
            logger.info(f"Found: {len(skills)} overlapping skills")
            logger.info(f"Duration: {duration:.2f}s")
            if skills:
                logger.info(f"Skills: {', '.join(skills[:10])}{'...' if len(skills) > 10 else ''}")
            logger.info("=" * 80)
            
            return skills
        
        except Exception as e:
            duration = time.time() - start_time
            logger.error("=" * 80)
            logger.error(f"❌ FAILED TO EXTRACT OVERLAPPING SKILLS")
            logger.error(f"Error: {str(e)}")
            logger.error(f"Duration before failure: {duration:.2f}s")
            logger.error("=" * 80)
            logger.error("Full error details:", exc_info=True)
            return []
    
    def identify_skill_gaps(self, resume_text: str, job_description: str) -> List[Dict]:
        """
        Identify skills mentioned in job description but missing or weak in resume
        
        Returns:
            List of dicts with 'skill', 'importance' (high/medium/low), and 'suggestion'
        """
        logger.info("=" * 80)
        logger.info("⚠️ IDENTIFYING SKILL GAPS")
        logger.info("=" * 80)
        
        start_time = time.time()
        
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
        
        logger.debug("Sending skill gap identification request to OpenAI")
        
        try:
            response = self.client.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                operation="identify_skill_gaps"
            )
            
            logger.debug("Parsing skill gaps response")
            result = json.loads(response)
            gaps = result.get("gaps", [])
            
            # Log gap statistics
            high_priority = len([g for g in gaps if g.get('importance') == 'high'])
            medium_priority = len([g for g in gaps if g.get('importance') == 'medium'])
            low_priority = len([g for g in gaps if g.get('importance') == 'low'])
            
            duration = time.time() - start_time
            logger.info("=" * 80)
            logger.info(f"✅ SKILL GAP IDENTIFICATION COMPLETE")
            logger.info(f"Total gaps identified: {len(gaps)}")
            logger.info(f"  - HIGH priority: {high_priority}")
            logger.info(f"  - MEDIUM priority: {medium_priority}")
            logger.info(f"  - LOW priority: {low_priority}")
            logger.info(f"Duration: {duration:.2f}s")
            
            # Log first few gaps as examples
            if gaps:
                logger.debug("Sample gaps:")
                for gap in gaps[:3]:
                    logger.debug(f"  - [{gap.get('importance', 'N/A')}] {gap.get('skill', 'N/A')}")
            
            logger.info("=" * 80)
            
            return gaps
        
        except Exception as e:
            duration = time.time() - start_time
            logger.error("=" * 80)
            logger.error(f"❌ FAILED TO IDENTIFY SKILL GAPS")
            logger.error(f"Error: {str(e)}")
            logger.error(f"Duration before failure: {duration:.2f}s")
            logger.error("=" * 80)
            logger.error("Full error details:", exc_info=True)
            return []
    
    def generate_executive_summary(self, resume_text: str, job_description: str, 
                                   overall_score: float, overlapping_skills: List[str],
                                   skill_gaps: List[Dict]) -> str:
        """
        Generate an executive summary of the analysis
        
        Returns:
            Executive summary text
        """
        logger.info("=" * 80)
        logger.info("📝 GENERATING EXECUTIVE SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Overall score: {overall_score}/100")
        logger.info(f"Overlapping skills: {len(overlapping_skills)}")
        logger.info(f"Skill gaps: {len(skill_gaps)}")
        
        start_time = time.time()
        
        high_priority_gaps = len([g for g in skill_gaps if g.get('importance') == 'high'])
        logger.info(f"High-priority gaps: {high_priority_gaps}")
        
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
High-Priority Gaps: {high_priority_gaps}

Job Description:
{job_description[:500]}...

Resume:
{resume_text[:500]}...

Write an executive summary."""
        
        try:
            response = self.client.structured_completion(
                system_prompt, 
                user_prompt,
                operation="generate_executive_summary"
            )
            summary = response.strip()
            
            duration = time.time() - start_time
            logger.info("=" * 80)
            logger.info(f"✅ EXECUTIVE SUMMARY GENERATED")
            logger.info(f"Summary length: {len(summary)} characters")
            logger.info(f"Duration: {duration:.2f}s")
            logger.debug(f"Summary: {summary}")
            logger.info("=" * 80)
            
            return summary
        
        except Exception as e:
            duration = time.time() - start_time
            logger.error("=" * 80)
            logger.error(f"❌ FAILED TO GENERATE EXECUTIVE SUMMARY")
            logger.error(f"Error: {str(e)}")
            logger.error(f"Duration before failure: {duration:.2f}s")
            logger.error("=" * 80)
            logger.error("Full error details:", exc_info=True)
            
            # Return fallback summary
            fallback = f"This resume shows a {overall_score}% fit for the target role based on our analysis."
            logger.info(f"Using fallback summary: {fallback}")
            return fallback
    
    def analyze_resume(self, resume_text: str, job_description: str) -> Dict:
        """
        Perform complete resume analysis
        
        Returns:
            Comprehensive analysis results
        """
        logger.info("*" * 80)
        logger.info("🚀 STARTING COMPREHENSIVE RESUME ANALYSIS")
        logger.info("*" * 80)
        logger.info(f"Resume length: {len(resume_text)} characters")
        logger.info(f"Job description length: {len(job_description)} characters")
        
        overall_start_time = time.time()
        
        try:
            # Extract overlapping skills
            logger.info("\n👉 STEP 1/5: Extracting overlapping skills")
            overlapping_skills = self.extract_overlapping_skills(resume_text, job_description)
            
            # Identify skill gaps
            logger.info("\n👉 STEP 2/5: Identifying skill gaps")
            skill_gaps = self.identify_skill_gaps(resume_text, job_description)
            
            # Evaluate all dimensions
            logger.info("\n👉 STEP 3/5: Evaluating dimensions")
            dimension_results = self.scoring_engine.evaluate_all_dimensions(resume_text, job_description)
            
            # Generate overall recommendations
            logger.info("\n👉 STEP 4/5: Generating recommendations")
            overall_recommendations = self.scoring_engine.generate_overall_recommendations(dimension_results)
            
            # Generate executive summary
            logger.info("\n👉 STEP 5/5: Generating executive summary")
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
            
            total_duration = time.time() - overall_start_time
            
            logger.info("*" * 80)
            logger.info("✅ COMPREHENSIVE RESUME ANALYSIS COMPLETE")
            logger.info("*" * 80)
            logger.info(f"Overall Score: {analysis['overall_score']}/100")
            logger.info(f"Overlapping Skills: {len(overlapping_skills)}")
            logger.info(f"Skill Gaps: {len(skill_gaps)}")
            logger.info(f"Dimensions Evaluated: {len(ScoringEngine.DIMENSIONS)}")
            logger.info(f"Recommendations Generated: {len(overall_recommendations)}")
            logger.info(f"Total Analysis Duration: {total_duration:.2f}s ({total_duration/60:.2f} minutes)")
            logger.info("*" * 80)
            
            return analysis
            
        except Exception as e:
            total_duration = time.time() - overall_start_time
            logger.error("*" * 80)
            logger.error("❌ COMPREHENSIVE RESUME ANALYSIS FAILED")
            logger.error("*" * 80)
            logger.error(f"Error: {str(e)}")
            logger.error(f"Duration before failure: {total_duration:.2f}s")
            logger.error("*" * 80)
            logger.error("Full error details:", exc_info=True)
            raise

