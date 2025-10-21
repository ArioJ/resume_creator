import json
from typing import Dict, List
import time

# Import centralized logging
from utils.logging_config import get_logger

from utils.openai_client import get_openai_client

logger = get_logger(__name__)


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
        logger.info("Initializing ScoringEngine")
        logger.info(f"Dimensions: {len(self.DIMENSIONS)}")
        for dim, weight in self.DIMENSION_WEIGHTS.items():
            logger.debug(f"  - {dim}: {weight*100:.0f}%")
        self.client = get_openai_client()
        logger.info("✓ ScoringEngine initialized")
    
    def evaluate_dimension(self, dimension: str, resume_text: str, job_description: str) -> Dict:
        """
        Evaluate a single dimension
        
        Returns:
            Dict with 'score', 'analysis', and 'recommendations'
        """
        logger.info(f"📊 Evaluating dimension: {dimension}")
        logger.debug(f"Weight: {self.DIMENSION_WEIGHTS.get(dimension, 0)*100:.0f}%")
        
        start_time = time.time()
        
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
                response_format={"type": "json_object"},
                operation=f"evaluate_dimension_{dimension.lower().replace(' ', '_')}"
            )
            
            result = json.loads(response)
            
            # Validate response structure
            if not all(key in result for key in ["score", "analysis", "recommendations"]):
                logger.warning(f"Invalid response structure for {dimension}, using defaults")
                raise ValueError("Invalid response structure from OpenAI")
            
            # Ensure score is within range
            result["score"] = max(0, min(100, result["score"]))
            
            duration = time.time() - start_time
            logger.info(f"✅ {dimension}: Score = {result['score']}/100 ({duration:.2f}s)")
            logger.debug(f"Analysis: {result['analysis'][:100]}...")
            logger.debug(f"Recommendations: {len(result['recommendations'])} items")
            
            return result
        
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ Failed to evaluate {dimension}: {str(e)} ({duration:.2f}s)", exc_info=True)
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
        logger.info("=" * 80)
        logger.info("📊 EVALUATING ALL DIMENSIONS")
        logger.info("=" * 80)
        logger.info(f"Total dimensions to evaluate: {len(self.DIMENSIONS)}")
        
        overall_start_time = time.time()
        results = {}
        
        for i, dimension in enumerate(self.DIMENSIONS, 1):
            logger.info(f"\n[{i}/{len(self.DIMENSIONS)}] Evaluating: {dimension}")
            results[dimension] = self.evaluate_dimension(dimension, resume_text, job_description)
        
        # Calculate weighted overall score
        logger.info("\nCalculating overall weighted score...")
        overall_score = sum(
            results[dim]["score"] * self.DIMENSION_WEIGHTS[dim]
            for dim in self.DIMENSIONS
        )
        overall_score = round(overall_score, 1)
        
        results["overall_score"] = overall_score
        results["dimension_weights"] = self.DIMENSION_WEIGHTS
        
        total_duration = time.time() - overall_start_time
        
        logger.info("=" * 80)
        logger.info("✅ ALL DIMENSIONS EVALUATED")
        logger.info("=" * 80)
        logger.info(f"Overall Score: {overall_score}/100")
        logger.info(f"Total Duration: {total_duration:.2f}s ({total_duration/60:.2f} minutes)")
        
        # Log breakdown
        logger.info("\nDimension Breakdown:")
        for dim in self.DIMENSIONS:
            score = results[dim]["score"]
            weight = self.DIMENSION_WEIGHTS[dim]
            contribution = score * weight
            logger.info(f"  {dim:45s} | Score: {score:3.0f} | Weight: {weight*100:2.0f}% | Contribution: {contribution:5.1f}")
        
        logger.info("=" * 80)
        
        return results
    
    def generate_overall_recommendations(self, dimension_results: Dict) -> List[str]:
        """
        Generate prioritized overall recommendations based on dimension scores
        
        Args:
            dimension_results: Results from evaluate_all_dimensions
        
        Returns:
            List of prioritized recommendations
        """
        logger.info("=" * 80)
        logger.info("💡 GENERATING OVERALL RECOMMENDATIONS")
        logger.info("=" * 80)
        
        # Identify weakest dimensions (score < 70)
        weak_dimensions = [
            (dim, data["score"]) 
            for dim, data in dimension_results.items()
            if dim in self.DIMENSIONS and data["score"] < 70
        ]
        
        # Sort by score (lowest first)
        weak_dimensions.sort(key=lambda x: x[1])
        
        logger.info(f"Identified {len(weak_dimensions)} dimensions scoring below 70")
        for dim, score in weak_dimensions:
            logger.debug(f"  - {dim}: {score}/100")
        
        recommendations = []
        
        # Add top recommendations from weakest dimensions
        focus_count = min(3, len(weak_dimensions))
        logger.info(f"Focusing on top {focus_count} weakest dimensions")
        
        for dim, score in weak_dimensions[:focus_count]:
            dim_recommendations = dimension_results[dim].get("recommendations", [])
            if dim_recommendations:
                recommendation = f"**{dim}** (Score: {score}): {dim_recommendations[0]}"
                recommendations.append(recommendation)
                logger.debug(f"Added recommendation for {dim}")
        
        # If all dimensions are strong, still provide improvement suggestions
        if not recommendations:
            logger.info("All dimensions scored above 70 - providing general improvement suggestions")
            recommendations.append("Your resume is strong overall. Continue to tailor it specifically to each job application.")
            recommendations.append("Consider adding more quantifiable achievements and metrics.")
            recommendations.append("Keep your resume updated with your latest skills and accomplishments.")
        
        logger.info("=" * 80)
        logger.info(f"✅ GENERATED {len(recommendations)} RECOMMENDATIONS")
        logger.info("=" * 80)
        
        return recommendations

