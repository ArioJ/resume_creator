import time
from typing import Dict
from pathlib import Path

# Import centralized logging
from utils.logging_config import get_logger
from utils.openai_client import get_openai_client

logger = get_logger(__name__)


class ResumeGenerator:
    """Generates optimized resumes tailored to job descriptions using LLM"""
    
    def __init__(self):
        logger.info("Initializing ResumeGenerator")
        self.client = get_openai_client()
        logger.info("✓ ResumeGenerator initialized")
    
    def generate_optimized_resume(self, resume_text: str, job_description: str) -> str:
        """
        Generate an optimized resume tailored to the job description
        
        Args:
            resume_text: Original resume text
            job_description: Target job description
        
        Returns:
            Optimized resume text
        """
        logger.info("=" * 80)
        logger.info("📝 GENERATING OPTIMIZED RESUME")
        logger.info("=" * 80)
        logger.info(f"Resume length: {len(resume_text)} characters")
        logger.info(f"Job description length: {len(job_description)} characters")
        
        start_time = time.time()
        
        try:
            # Construct the prompt
            prompt = self._build_generation_prompt(resume_text, job_description)
            
            logger.info("Calling OpenAI API for resume generation...")
            
            # Call OpenAI API
            response = self.client.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert resume writer and career advisor. Your task is to optimize resumes to better align with specific job descriptions while maintaining complete authenticity and realism.

CRITICAL RULES:
1. NEVER fabricate or add experiences, skills, or achievements that are not present in the original resume
2. ONLY reorganize, rephrase, and emphasize existing content
3. Use industry-standard keywords from the job description where they genuinely match the candidate's experience
4. Maintain the candidate's authentic career trajectory and timeline
5. Keep all dates, company names, and job titles exactly as they appear in the original resume
6. If the candidate lacks a required skill, DO NOT add it - instead, highlight transferable skills
7. The optimized resume should be realistic and truthful"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            optimized_resume = response.strip()
            
            duration = time.time() - start_time
            
            logger.info("=" * 80)
            logger.info("✅ OPTIMIZED RESUME GENERATED")
            logger.info("=" * 80)
            logger.info(f"Generated resume length: {len(optimized_resume)} characters")
            logger.info(f"Duration: {duration:.2f}s")
            logger.info("=" * 80)
            
            return optimized_resume
        
        except Exception as e:
            duration = time.time() - start_time
            logger.error("=" * 80)
            logger.error("❌ RESUME GENERATION FAILED")
            logger.error("=" * 80)
            logger.error(f"Error: {str(e)}")
            logger.error(f"Duration before failure: {duration:.2f}s")
            logger.error("=" * 80)
            logger.error("Full error details:", exc_info=True)
            raise
    
    def _build_generation_prompt(self, resume_text: str, job_description: str) -> str:
        """Build the prompt for resume generation"""
        
        prompt = f"""I need you to optimize the following resume to better align with a specific job description while maintaining COMPLETE AUTHENTICITY.

**IMPORTANT CONSTRAINTS:**
- DO NOT add any skills, experiences, or achievements not present in the original resume
- DO NOT fabricate or exaggerate any information
- ONLY rephrase, reorganize, and emphasize existing content
- Keep all dates, company names, and positions exactly as stated
- Use relevant keywords from the job description ONLY where they genuinely match existing experience
- If a required skill is missing, highlight transferable or related skills instead

**ORIGINAL RESUME:**
```
{resume_text}
```

**TARGET JOB DESCRIPTION:**
```
{job_description}
```

**YOUR TASK:**
1. Analyze the job description to identify key requirements, skills, and qualifications
2. Review the candidate's actual experience and skills from their original resume
3. Reorganize and rephrase the resume to emphasize experiences that align with the job requirements
4. Use industry-standard keywords from the job description where they genuinely apply
5. Highlight transferable skills that relate to the job requirements
6. Structure the resume to make relevant experience more prominent
7. Ensure the tone and language match the industry standards of the target role

**FORMAT:**
Provide the optimized resume in **Markdown format**. Use the following structure:

```markdown
# [Candidate Name]

[Contact Information]

## Professional Summary
[Compelling 2-3 sentence summary optimized for the role]

## Work Experience

### [Job Title] | [Company Name]
*[Start Date] - [End Date]*

- [Achievement/responsibility using relevant keywords]
- [Achievement/responsibility highlighting transferable skills]
- [Continue with bullet points]

### [Next Job Title] | [Company Name]
*[Start Date] - [End Date]*
...

## Skills

**Technical Skills:** [List relevant technical skills]
**Tools & Technologies:** [List tools and technologies]
**Soft Skills:** [List relevant soft skills]

## Education

**[Degree]** | [Institution Name]
*[Graduation Date]*
[Relevant details]

## Certifications
[If present and relevant]

## Projects
[If present and relevant]
```

**REMEMBER:** The resume must be 100% truthful and based ONLY on information present in the original resume. Your goal is to present the candidate's real experience in the most compelling way for this specific role.

Generate the optimized resume in Markdown format now:"""
        
        return prompt


def get_resume_generator():
    """Get or create a singleton instance of ResumeGenerator"""
    global _generator_instance
    if '_generator_instance' not in globals():
        _generator_instance = ResumeGenerator()
    return _generator_instance

