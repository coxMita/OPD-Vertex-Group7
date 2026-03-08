"""Prompt templates for the AI service."""

CHUNK_SUMMARY_PROMPT_TEMPLATE = """\
You are a clinical assistant. Read the following excerpt from a medical \
consultation transcript and extract any medically relevant information \
(symptoms, findings, diagnoses, medications, dosages, frequencies, vitals, instructions). \
Write 1-2 sentences preserving specific medical details like drug names, \
dosages, frequencies, and vital signs exactly as stated. \
Only respond with NO_MEDICAL_CONTENT if the excerpt contains absolutely \
zero medical information — no symptoms, no drugs, no findings, nothing clinical at all.

Excerpt:
{chunk}

Medical summary:"""

SUMMARY_PROMPT_TEMPLATE = """\
You are a clinical assistant. Based on the following raw excerpts from a \
medical consultation transcript, produce a concise clinical summary (3-5 sentences). \
Focus on the patient's chief complaint, key findings including any vitals, \
the diagnosis, and all decisions made including medications and follow-up. \
Do not repeat the same word or phrase twice in the same sentence. \
Use only information present in the excerpts — do not invent or assume anything.

Transcript excerpts:
{transcript}

Clinical Summary:"""

PRESCRIPTION_PROMPT_TEMPLATE = """\
You are a clinical assistant. Based on the following excerpts from a medical \
consultation transcript, extract the PRIMARY medication prescribed for the \
patient's condition and return it ONLY as a valid JSON object with this exact \
structure — no extra text, no markdown, no explanation:

{{
  "medication_name": "<single drug name only, e.g. Paracetamol — never combine two drugs here — never write 'none'>",
  "dosage": "<dose amount ONLY if explicitly stated in the transcript, e.g. 500mg — null if not mentioned>",
  "frequency": "<exact frequency as stated in the transcript, e.g. once daily after lunch — never infer or guess>",
  "duration": "<ONLY if the doctor explicitly stated a time period for taking the medication — null if not stated, never guess>",
  "notes": "<list each secondary medication as: DrugName — frequency. Add warnings after. null only if truly nothing extra.>"
}}

Rules:
- medication_name must be ONE drug only — the primary one the doctor prescribed
- medication_name must NEVER be the string "none" or empty — always pick the most clinically significant drug; only use the JSON null fallback at the bottom if truly nothing was prescribed
- if multiple drugs are prescribed, put the primary one in medication_name and list ALL others in notes with their individual frequency
- dosage and frequency must come ONLY from words explicitly spoken in the transcript — never infer, assume, or guess
- if the transcript says "once after lunch", frequency must be "once daily after lunch"
- duration refers ONLY to how long to take the medication, never to physical restrictions or recovery time
- if duration is not explicitly spoken in the transcript, it must be null — never write a typical or assumed duration
- if the doctor explicitly said NOT to prescribe antibiotics or any drug, notes must mention this
- notes should be null only if there is truly nothing extra to mention

If no medication at all was prescribed, return:
{{"medication_name": null, "dosage": null, "frequency": null,
  "duration": null, "notes": "No prescription indicated."}}

Transcript excerpts:
{transcript}

JSON:"""
