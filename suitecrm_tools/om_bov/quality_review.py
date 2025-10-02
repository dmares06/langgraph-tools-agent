"""Quality review tools for OM/BOV content."""

import json
from langchain_core.tools import tool

@tool 
def review_om_quality(
    content: str, 
    document_type: str = "OM",
    review_type: str = "comprehensive"
) -> str:
    """
    Review and provide quality feedback on OM/BOV content for improvements.
    
    Args:
        content: The OM or BOV content to review
        document_type: Type of document ("OM", "BOV")
        review_type: Type of review ("grammar", "completeness", "persuasiveness", "comprehensive")
    
    Returns:
        JSON string with quality assessment and improvement suggestions
    """
    try:
        content_length = len(content)
        word_count = len(content.split())
        
        quality_score = 0
        feedback = []
        suggestions = []
        
        # Document type specific criteria
        if document_type.upper() == "BOV":
            # BOV-specific quality checks
            valuation_terms = ["cap rate", "NOI", "market value", "comparable", "valuation", "approach"]
            valuation_score = sum(1 for term in valuation_terms if term.lower() in content.lower())
            
            if valuation_score >= 4:
                quality_score += 30
                feedback.append("Strong valuation methodology and terminology used.")
            else:
                suggestions.append("Include more valuation-specific terms and methodology")
                
            # Check for required BOV sections
            required_sections = ["income approach", "sales comparison", "market analysis"]
            section_mentions = sum(1 for section in required_sections if section.lower() in content.lower())
            
            if section_mentions >= 2:
                quality_score += 25
                feedback.append("Multiple valuation approaches referenced.")
            else:
                suggestions.append("Include references to income approach, sales comparison, and market analysis")
                
        else:  # OM-specific checks
            # Investment language check
            investment_terms = ["investment", "opportunity", "cash flow", "returns", "strategic"]
            investment_score = sum(1 for term in investment_terms if term.lower() in content.lower())
            
            if investment_score >= 4:
                quality_score += 25
                feedback.append("Strong investment language and positioning.")
            else:
                suggestions.append("Enhance investment appeal with stronger positioning language")
        
        # Common quality checks for both document types
        if word_count < 100:
            feedback.append(f"Content appears too brief for professional {document_type}. Consider expanding key sections.")
        elif word_count > 200:
            quality_score += 20
            feedback.append(f"Good content length for {document_type} section.")
        
        # Financial data inclusion
        financial_indicators = ["$", "NOI", "cap rate", "rental", "income", "expense", "price"]
        financial_mentions = sum(1 for indicator in financial_indicators if indicator.lower() in content.lower())
        if financial_mentions >= 3:
            quality_score += 25
            feedback.append("Strong financial data inclusion.")
        else:
            suggestions.append("Add more specific financial metrics and data points")
        
        # Professional presentation
        if not any(char.isdigit() for char in content):
            suggestions.append("Include specific numerical data (prices, sizes, dates)")
        if "location" not in content.lower():
            suggestions.append("Emphasize location benefits and accessibility")
            
        quality_score += min(20, len(content.split()) // 10)
        
        # Document-specific improvement suggestions
        if document_type.upper() == "BOV":
            suggestions.extend([
                "Include confidence level in valuation conclusion",
                "Add market conditions disclaimer",
                "Reference data sources and methodology"
            ])
        else:
            suggestions.extend([
                "Highlight unique value propositions",
                "Include call-to-action for interested investors",
                "Add broker contact information"
            ])
        
        return json.dumps({
            "success": True,
            "document_type": document_type,
            "review_type": review_type,
            "quality_score": min(quality_score, 100),
            "word_count": word_count,
            "character_count": content_length,
            "strengths": feedback,
            "improvement_suggestions": suggestions[:8],  # Limit suggestions
            "overall_assessment": (
                "Professional" if quality_score >= 70 
                else "Needs Enhancement" if quality_score >= 50 
                else "Requires Significant Improvement"
            ),
            "document_specific_notes": f"{document_type} requirements {'met' if quality_score >= 60 else 'need attention'}",
            "next_steps": f"Implement suggested improvements for {document_type} standards"
        }, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to review {document_type} content quality: {str(e)}"
        })