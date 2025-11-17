"""Gemini AI service for intelligent mapping and validation."""
import json
import logging
from typing import Dict, List, Optional

from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel, Part
from config import settings

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for interacting with Vertex AI Gemini models."""
    
    def __init__(self):
        """Initialize Gemini service."""
        try:
            aiplatform.init(
                project=settings.project_id,
                location=settings.vertex_ai_location
            )
            self.model = GenerativeModel(settings.vertex_ai_model)
        except Exception as e:
            logger.warning(f"Could not initialize Gemini service: {e}. Service will run in mock mode.")
            self.model = None
    
    async def map_to_coa(
        self,
        source_items: List[Dict],
        industry: str,
        canonical_coa: List[Dict]
    ) -> List[Dict]:
        """
        Map source financial statement line items to canonical chart of accounts.
        
        Args:
            source_items: List of source line items with name and value
            industry: Industry classification (e.g., "SaaS", "Manufacturing")
            canonical_coa: Canonical chart of accounts structure
            
        Returns:
            List of mappings with source, target, confidence, and reasoning
        """
        prompt = f"""You are an expert accountant with deep knowledge of financial statements across industries.

Your task is to map the following source financial statement line items to a canonical chart of accounts for a {industry} company.

SOURCE LINE ITEMS:
{json.dumps(source_items, indent=2)}

CANONICAL CHART OF ACCOUNTS:
{json.dumps(canonical_coa, indent=2)}

INSTRUCTIONS:
1. Map each source item to the most appropriate canonical account
2. Consider industry-specific terminology and conventions
3. Provide confidence scores (0.0 to 1.0):
   - > 0.9: High confidence (auto-apply)
   - 0.7-0.9: Medium confidence (needs review)
   - < 0.7: Low confidence (manual mapping required)
4. Explain your reasoning for each mapping

Return ONLY a valid JSON array with this exact structure:
[
  {{
    "source_id": "source item identifier",
    "source_name": "original source line item name",
    "target_id": "canonical account identifier",
    "target_name": "canonical account name",
    "confidence": 0.95,
    "reasoning": "Clear explanation of why this mapping makes sense"
  }}
]

CRITICAL: Return ONLY the JSON array, no additional text or explanation outside the JSON."""

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Clean up response (remove markdown code blocks if present)
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            
            mappings = json.loads(result_text)
            logger.info(f"Successfully mapped {len(mappings)} items")
            return mappings
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            logger.error(f"Response text: {result_text}")
            raise ValueError(f"Invalid JSON response from Gemini: {e}")
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            raise
    
    async def validate_financials(self, data: Dict) -> Dict:
        """
        AI-powered validation of financial data.
        
        Args:
            data: Financial data to validate (income statement, balance sheet, etc.)
            
        Returns:
            Validation results with issues and quality score
        """
        prompt = f"""You are a forensic accountant reviewing financial statements for accuracy and consistency.

FINANCIAL DATA TO REVIEW:
{json.dumps(data, indent=2)}

YOUR TASKS:
1. Identify red flags or anomalies (unusual ratios, inconsistencies, missing data)
2. Check for mathematical consistency (e.g., Assets = Liabilities + Equity)
3. Compare metrics to typical industry standards
4. Suggest corrections if issues are found
5. Assess overall data quality

VALIDATION RULES:
- Revenue should be positive (or explain if negative)
- Gross profit = Revenue - COGS
- Operating expenses should be reasonable relative to revenue
- Balance sheet should balance
- Cash flow should reconcile with balance sheet changes

Return ONLY a valid JSON object with this structure:
{{
  "issues": [
    {{
      "severity": "error|warning|info",
      "category": "consistency|completeness|accuracy|reasonableness",
      "description": "Clear description of the issue",
      "affected_items": ["item1", "item2"],
      "suggestion": "How to fix or what to review",
      "impact": "high|medium|low"
    }}
  ],
  "quality_score": 8.5,
  "summary": "Overall assessment in 2-3 sentences",
  "recommendations": [
    "Specific action item 1",
    "Specific action item 2"
  ]
}}

CRITICAL: Return ONLY the JSON object, no additional text."""

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Clean up response
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            
            validation_results = json.loads(result_text)
            logger.info(f"Validation complete with quality score: {validation_results.get('quality_score', 'N/A')}")
            return validation_results
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini validation response: {e}")
            raise ValueError(f"Invalid JSON response from Gemini: {e}")
        except Exception as e:
            logger.error(f"Error calling Gemini API for validation: {e}")
            raise
    
    async def generate_forecast_assumptions(
        self,
        historical_data: Dict,
        industry: str,
        market_conditions: Optional[Dict] = None
    ) -> Dict:
        """
        Generate intelligent forecast assumptions based on historical data.
        
        Args:
            historical_data: Historical financial data
            industry: Industry classification
            market_conditions: Optional market conditions and trends
            
        Returns:
            Forecast assumptions and rationale
        """
        market_context = f"\n\nMARKET CONDITIONS:\n{json.dumps(market_conditions, indent=2)}" if market_conditions else ""
        
        prompt = f"""You are a financial analyst creating forecast assumptions for a {industry} company.

HISTORICAL FINANCIAL DATA:
{json.dumps(historical_data, indent=2)}{market_context}

TASKS:
1. Analyze historical trends (revenue growth, margins, efficiency ratios)
2. Consider industry benchmarks and market conditions
3. Propose reasonable forecast assumptions for next 5 years
4. Explain the rationale for each assumption

Return ONLY a valid JSON object:
{{
  "revenue_growth": {{
    "year_1": 0.15,
    "year_2": 0.12,
    "year_3": 0.10,
    "year_4": 0.08,
    "year_5": 0.06,
    "rationale": "Explanation based on historical trends and market"
  }},
  "gross_margin": {{
    "baseline": 0.65,
    "trend": "improving|stable|declining",
    "rationale": "Explanation"
  }},
  "operating_expenses": {{
    "rd_percent_revenue": 0.15,
    "sales_marketing_percent_revenue": 0.35,
    "ga_percent_revenue": 0.10,
    "rationale": "Explanation"
  }},
  "capital_expenditure": {{
    "percent_revenue": 0.05,
    "rationale": "Explanation"
  }},
  "working_capital": {{
    "days_receivable": 45,
    "days_inventory": 30,
    "days_payable": 30,
    "rationale": "Explanation"
  }},
  "key_risks": [
    "Risk factor 1",
    "Risk factor 2"
  ],
  "key_opportunities": [
    "Opportunity 1",
    "Opportunity 2"
  ]
}}"""

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            
            assumptions = json.loads(result_text)
            logger.info("Generated forecast assumptions successfully")
            return assumptions
            
        except Exception as e:
            logger.error(f"Error generating forecast assumptions: {e}")
            raise
    
    async def chat_response(
        self,
        user_message: str,
        context: Dict,
        conversation_history: List[Dict]
    ) -> str:
        """
        Generate conversational AI response for valuation questions.
        
        Args:
            user_message: User's question or request
            context: Current engagement context (financials, valuation, etc.)
            conversation_history: Previous messages in conversation
            
        Returns:
            AI assistant response
        """
        history_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in conversation_history[-5:]  # Last 5 messages
        ])
        
        prompt = f"""You are a helpful valuation assistant with expertise in financial analysis, DCF modeling, and business valuation.

ENGAGEMENT CONTEXT:
{json.dumps(context, indent=2)}

CONVERSATION HISTORY:
{history_text}

USER MESSAGE:
{user_message}

INSTRUCTIONS:
- Answer questions clearly and concisely
- Reference specific numbers from the context when relevant
- If asked to adjust assumptions, explain the impact
- If asked about calculations, show your work
- Be professional but conversational
- If you don't have enough information, ask clarifying questions

Respond naturally to the user's message."""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating chat response: {e}")
            raise


# Global instance
gemini_service = GeminiService()
