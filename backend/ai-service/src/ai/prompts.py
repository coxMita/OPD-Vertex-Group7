"""Prompt templates for the AI service."""

SUMMARY_PROMPT_TEMPLATE = """\
You are a clinical assistant. Based on the following excerpts from a medical \
consultation transcript, produce a concise clinical summary (3-5 sentences). \
Focus on the patient's chief complaint, key findings, and decisions made.

Transcript excerpts:
{transcript}

Clinical Summary:"""

PRESCRIPTION_PROMPT_TEMPLATE = """\
You are a clinical assistant. Based on the following excerpts from a medical \
consultation transcript, extract the PRIMARY medication prescribed for the \
patient's condition and return it ONLY as a valid JSON object with this exact \
structure — no extra text, no markdown, no explanation:

{{
  "medication_name": "<name of the drug only, e.g. Paracetamol>",
  "dosage": "<dose amount only, e.g. 500mg>",
  "frequency": "<how often to take it, e.g. three times a day>",
  "duration": "<how long to take the medication, e.g. 7 days or as needed — NOT activity restrictions>",
  "notes": "<any important warnings or secondary medications mentioned, or null if none>"
}}

Rules:
- duration refers ONLY to how long to take the medication, never to physical restrictions or recovery time
- if the doctor explicitly said NOT to prescribe antibiotics or any drug, notes must mention this
- if a secondary medication is also mentioned, include it in notes
- notes should be null only if there is truly nothing extra to mention

If no medication at all was prescribed, return:
{{"medication_name": null, "dosage": null, "frequency": null,
  "duration": null, "notes": "No prescription indicated."}}

Transcript excerpts:
{transcript}

JSON:"""
