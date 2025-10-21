import json
import logging
from typing import Dict, List
from utils.openai_client import get_openai_client

logger = logging.getLogger(__name__)


class ScoringEngine:
    """Evaluates resumes across multiple dimensions using OpenAI"""
    
    # Define the 9 evaluation dimensions
    DIMENSIONS = [
        "Relevance of Experience",
        "Impact and Achievements",
        "Technical Proficiency",
        "Clarity and Structure",
        "Quantifiable Results",
        "Communication and Writing Quality",
        "Growth and Progression",
        "Innovation and Problem-Solving",
        "ATS Compatibility"
    ]
    
    # Weights for calculating overall score (must sum to 1.0)
    DIMENSION_WEIGHTS = {
        "Relevance of Experience": 0.20,
        "Impact and Achievements": 0.15,
        "Technical Proficiency": 0.15,
        "Clarity and Structure": 0.10,
        "Quantifiable Results": 0.10,
        "Communication and Writing Quality": 0.08,
        "Growth and Progression": 0.08,
        "Innovation and Problem-Solving": 0.09,
        "ATS Compatibility": 0.05
    }
    
    def __init__(self):
        self.client = get_openai_client()
    
    def evaluate_dimension(self, dimension: str, resume_text: str, job_description: str) -> Dict:
        """
        Evaluate a single dimension
        
        Returns:
            Dict with 'score', 'analysis', and 'recommendations'
        """
        system_prompt = f"""You are an expert resume evaluator. Analyze the resume against the job description 
for the dimension: {dimension}.

Provide a detailed evaluation with:
1. A score from 0-100 (be realistic and critical)
2. A detailed analysis (2-3 sentences explaining the score)
3. Specific recommendations for improvement (2-3 actionable items)

Return your response as valid JSON with this exact structure:
{{
    "score": <number 0-100>,
    "analysis": "<detailed explanation>",
    "recommendations": ["<recommendation 1>", "<recommendation 2>", "<recommendation 3>"]
}}"""
        
        user_prompt = f"""Job Description:
{job_description}

---

Resume:
{resume_text}

---

Evaluate this resume for: {dimension}"""
        
        try:
            response = self.client.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response)
            
            # Validate response structure
            if not all(key in result for key in ["score", "analysis", "recommendations"]):
                raise ValueError("Invalid response structure from OpenAI")
            
            # Ensure score is within range
            result["score"] = max(0, min(100, result["score"]))
            
            logger.info(f"Evaluated {dimension}: Score = {result['score']}")
            return result
        
        except Exception as e:
            logger.error(f"Failed to evaluate {dimension}: {e}")
            # Return default values on error
            return {
                "score": 0,
                "analysis": f"Error evaluating this dimension: {str(e)}",
                "recommendations": ["Unable to generate recommendations due to an error."]
            }
    
    def evaluate_all_dimensions(self, resume_text: str, job_description: str) -> Dict:
        """
        Evaluate resume across all 9 dimensions
        
        Returns:
            Dict with dimension scores and overall score
        """
        results = {}
        
        for dimension in self.DIMENSIONS:
            logger.info(f"Evaluating dimension: {dimension}")
            results[dimension] = self.evaluate_dimension(dimension, resume_text, job_description)
        
        # Calculate weighted overall score
        overall_score = sum(
            results[dim]["score"] * self.DIMENSION_WEIGHTS[dim]
            for dim in self.DIMENSIONS
        )
        
        results["overall_score"] = round(overall_score, 1)
        results["dimension_weights"] = self.DIMENSION_WEIGHTS
        
        logger.info(f"Overall score calculated: {results['overall_score']}")
        return results
    
    def generate_overall_recommendations(self, dimension_results: Dict) -> List[str]:
        """
        Generate prioritized overall recommendations based on dimension scores
        
        Args:
            dimension_results: Results from evaluate_all_dimensions
        
        Returns:
            List of prioritized recommendations
        """
        # Identify weakest dimensions (score < 70)
        weak_dimensions = [
            (dim, data["score"]) 
            for dim, data in dimension_results.items()
            if dim in self.DIMENSIONS and data["score"] < 70
        ]
        
        # Sort by score (lowest first)
        weak_dimensions.sort(key=lambda x: x[1])
        
        recommendations = []
        
        # Add top recommendations from weakest dimensions
        for dim, score in weak_dimensions[:3]:  # Focus on top 3 weakest
            dim_recommendations = dimension_results[dim].get("recommendations", [])
            if dim_recommendations:
                recommendations.append(f"**{dim}** (Score: {score}): {dim_recommendations[0]}")
        
        # If all dimensions are strong, still provide improvement suggestions
        if not recommendations:
            recommendations.append("Your resume is strong overall. Continue to tailor it specifically to each job application.")
            recommendations.append("Consider adding more quantifiable achievements and metrics.")
            recommendations.append("Keep your resume updated with your latest skills and accomplishments.")
        
        return recommendations

