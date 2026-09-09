import json
import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY is missing. Add it to Streamlit Secrets "
        "or a local .env file."
    )

client = Groq(api_key=GROQ_API_KEY)

# Keep this configurable through an environment variable.
MODEL_NAME = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

SYSTEM_PROMPT = """
You are BidGuard AI, an expert Tender and Bid Compliance Agent.

Your task is to analyze government and corporate tender documents
and compare tender requirements with bidder evidence.

Rules:
1. Never invent requirements, evidence, dates, amounts, or certificates.
2. Never mark a requirement COMPLIANT without supporting evidence.
3. If evidence is insufficient, use PARTIAL or MISSING.
4. Preserve exact amounts, dates, percentages and conditions.
5. Distinguish:
   COMPLIANT = evidence clearly satisfies the requirement.
   PARTIAL = some evidence exists but verification is incomplete.
   NON-COMPLIANT = evidence clearly fails the requirement.
   MISSING = required evidence was not supplied.
6. Be conservative when interpreting eligibility requirements.
7. Explain decisions using the supplied evidence.
8. Never provide a legal guarantee.
9. If the source does not contain an answer, say "Insufficient evidence".
10. The original tender document remains the final authority.
"""


class BidComplianceAgent:
    def __init__(self, model: str = MODEL_NAME, temperature: float = 0.1):
        self.client = client
        self.model = model
        self.temperature = temperature

    def _call_llm(
        self,
        prompt: str,
        json_mode: bool = False,
        max_tokens: int = 5000,
    ) -> str:
        kwargs = {
            "model": self.model,
            "temperature": self.temperature,
            "max_completion_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        }

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content or ""
        except Exception as exc:
            raise RuntimeError(f"Groq API error: {exc}") from exc

    @staticmethod
    def _parse_json(text: str) -> Dict[str, Any]:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {
                "error": "The model returned invalid JSON.",
                "raw_response": text,
            }

    def extract_requirements(self, tender_text: str) -> Dict[str, Any]:
        prompt = f"""
Extract the important compliance requirements from this tender.

Focus on:
- eligibility
- technical requirements
- financial requirements
- EMD and tender fee
- experience
- turnover
- certificates
- forms and undertakings
- GST/PAN/EPF/ESIC
- technical staff and machinery
- BOQ/price bid
- submission requirements
- important dates
- contract duration
- bid validity
- location
- tender value

Return ONLY JSON:

{{
  "tender_summary": {{
    "title": "",
    "organisation": "",
    "tender_id": "",
    "tender_reference": "",
    "tender_value": "",
    "location": "",
    "bid_validity_days": "",
    "work_period_days": ""
  }},
  "deadlines": {{
    "submission_deadline": "",
    "opening_date": "",
    "clarification_deadline": ""
  }},
  "requirements": [
    {{
      "id": "REQ-001",
      "category": "",
      "requirement": "",
      "mandatory": true,
      "required_evidence": [],
      "condition": "",
      "amount": "",
      "deadline": "",
      "source": ""
    }}
  ]
}}

TENDER:
{tender_text}
"""
        return self._parse_json(
            self._call_llm(prompt, json_mode=True, max_tokens=8000)
        )

    def analyze_bidder_documents(self, documents_text: str) -> Dict[str, Any]:
        prompt = f"""
Extract verifiable bidder information from the supplied documents.

Look for:
- company name
- GST/PAN/EPF/ESIC
- registrations
- turnover
- bank solvency
- previous/similar work
- completion certificates
- staff
- machinery
- EMD
- tender fee
- certifications
- dates
- amounts
- other relevant evidence

Do not assume anything that is not present.

Return ONLY JSON:

{{
  "bidder_profile": {{
    "company_name": "",
    "gst_available": false,
    "pan_available": false,
    "epf_available": false,
    "esic_available": false
  }},
  "financial_information": {{
    "turnover": [],
    "bank_solvency": ""
  }},
  "experience": [],
  "certificates": [],
  "documents": [
    {{
      "document_name": "",
      "document_type": "",
      "available": true,
      "key_information": ""
    }}
  ]
}}

BIDDER DOCUMENTS:
{documents_text}
"""
        return self._parse_json(
            self._call_llm(prompt, json_mode=True, max_tokens=7000)
        )

    def check_compliance(
        self,
        requirements: List[Dict[str, Any]],
        bidder_information: Dict[str, Any],
    ) -> Dict[str, Any]:
        prompt = f"""
Compare every tender requirement with bidder information.

TENDER REQUIREMENTS:
{json.dumps(requirements, indent=2)}

BIDDER INFORMATION:
{json.dumps(bidder_information, indent=2)}

For every requirement return:
- requirement_id
- requirement
- status
- evidence
- missing_information
- explanation
- risk
- confidence

Statuses:
COMPLIANT, PARTIAL, NON-COMPLIANT, MISSING

Risks:
LOW, MEDIUM, HIGH, CRITICAL

Return ONLY JSON:

{{
  "compliance_results": [
    {{
      "requirement_id": "",
      "requirement": "",
      "status": "",
      "evidence": "",
      "missing_information": "",
      "explanation": "",
      "risk": "",
      "confidence": 0
    }}
  ],
  "summary": {{
    "total_requirements": 0,
    "compliant": 0,
    "partial": 0,
    "non_compliant": 0,
    "missing": 0
  }}
}}
"""
        return self._parse_json(
            self._call_llm(prompt, json_mode=True, max_tokens=10000)
        )

    def calculate_score(self, compliance_results: Dict[str, Any]) -> Dict[str, Any]:
        summary = compliance_results.get("summary", {})

        total = int(summary.get("total_requirements", 0) or 0)
        compliant = int(summary.get("compliant", 0) or 0)
        partial = int(summary.get("partial", 0) or 0)
        non_compliant = int(summary.get("non_compliant", 0) or 0)
        missing = int(summary.get("missing", 0) or 0)

        if total == 0:
            return {
                "score": 0,
                "recommendation": "INSUFFICIENT DATA",
                "total_requirements": 0,
                "compliant": 0,
                "partial": 0,
                "non_compliant": 0,
                "missing": 0,
            }

        score = round(((compliant + partial * 0.5) / total) * 100, 2)

        if non_compliant > 0:
            recommendation = "DO NOT BID"
        elif missing > 0:
            recommendation = "CONDITIONALLY RECOMMENDED"
        elif score >= 85:
            recommendation = "RECOMMENDED TO BID"
        elif score >= 70:
            recommendation = "CONDITIONALLY RECOMMENDED"
        else:
            recommendation = "HIGH RISK"

        return {
            "score": score,
            "recommendation": recommendation,
            "total_requirements": total,
            "compliant": compliant,
            "partial": partial,
            "non_compliant": non_compliant,
            "missing": missing,
        }

    def generate_recommendation(
        self, compliance_report: Dict[str, Any]
    ) -> str:
        prompt = f"""
Review this bid compliance analysis:

{json.dumps(compliance_report, indent=2)}

Write a concise professional recommendation containing:
1. overall recommendation
2. compliance score
3. strengths
4. critical risks
5. missing documents
6. actions before submission
7. warning that the original tender must be verified

Do not invent information.
"""
        return self._call_llm(prompt, max_tokens=3000)

    def ask(self, question: str, context: str) -> str:
        prompt = f"""
Answer the question using ONLY the supplied tender context.

QUESTION:
{question}

TENDER CONTEXT:
{context}

If the answer cannot be supported by the context, say:
"Insufficient evidence in the provided tender documents."

Do not invent information.
"""
        return self._call_llm(prompt, max_tokens=2500)

    def analyze_bid(
        self,
        tender_text: str,
        bidder_documents_text: str,
    ) -> Dict[str, Any]:
        requirements_data = self.extract_requirements(tender_text)
        bidder_data = self.analyze_bidder_documents(bidder_documents_text)

        requirements = requirements_data.get("requirements", [])
        compliance = self.check_compliance(requirements, bidder_data)
        score = self.calculate_score(compliance)

        final_report = self.generate_recommendation(
            {
                "tender": requirements_data.get("tender_summary", {}),
                "compliance": compliance,
                "score": score,
            }
        )

        return {
            "tender": requirements_data,
            "bidder": bidder_data,
            "compliance": compliance,
            "score": score,
            "recommendation": final_report,
        }
