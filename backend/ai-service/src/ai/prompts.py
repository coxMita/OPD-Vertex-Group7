"""Prompt templates for the AI service."""

SUMMARY_PROMPT_TEMPLATE = """\
You are a clinical assistant. Read the following medical consultation transcript and \
produce a concise clinical summary (3-5 sentences). Focus on the patient's chief \
complaint, key findings, and any decisions made during the consultation.

Transcript:
{transcript}

Clinical Summary:"""

PRESCRIPTION_PROMPT_TEMPLATE = """\
You are a clinical assistant. Based on the following medical consultation transcript, \
extract prescription information and return it ONLY as a valid JSON object with this \
exact structure — no extra text, no markdown, no explanation:

{{
  "medication_name": "<string>",
  "dosage": "<string>",
  "frequency": "<string>",
  "duration": "<string>",
  "notes": "<string or null>"
}}

If no prescription is indicated in the transcript, return:
If no prescription is indicated in the transcript, return:
{{"medication_name": null, "dosage": null, "frequency": null,
  "duration": null, "notes": "No prescription indicated."}}

Transcript:
{transcript}

JSON:"""
