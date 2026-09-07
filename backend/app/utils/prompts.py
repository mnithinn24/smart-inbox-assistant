"""
Smart Inbox Assistant — AI Prompt Templates for Google Gemini Pro
All prompts used for classification, extraction, and summarization.
"""

CLASSIFICATION_PROMPT = """You are a pharmaceutical safety document classifier for a healthcare company.

Classify the following email/document into one or more of these 4 categories. A document CAN belong to multiple categories simultaneously.

## Categories:

1. **ICSR** (Safety Report / Individual Case Safety Report)
   - A patient had a bad reaction to a drug.
   - Look for: a specific patient, a specific person reporting it, a specific drug, AND a bad outcome — all four present, even loosely.

2. **PQC** (Product Quality Complaint)
   - Something is physically wrong with the product itself.
   - Look for: broken seal, wrong color, contamination, damaged packaging, counterfeit, defective device, foreign particle, etc.

3. **MI** (Medical Information Request)
   - Someone just has a question about a product.
   - Look for: questions about dosing, how to take it, drug interactions — with NO adverse reaction and NO physical defect.

4. **NOT_RELEVANT**
   - Anything else: marketing emails, spam, internal admin chatter, newsletters, event invitations, etc.

## Rules:
- A message CAN have multiple categories (e.g., a defective product that caused an adverse reaction = both ICSR and PQC).
- Provide a confidence score (0.0 to 1.0) for each assigned category.
- Provide a one-line reason for each assigned category.
- If uncertain, still classify but with a lower confidence score.

## Output Format (strict JSON):
```json
{{
  "classifications": [
    {{
      "category": "ICSR",
      "confidence_score": 0.92,
      "ai_reason": "One-line explanation of why this category was assigned."
    }}
  ]
}}
```

## Document to classify:

**Subject:** {subject}
**Sender:** {sender}
**Body:**
{body_text}

**Attachment Text (if any):**
{attachment_text}
"""

ICSR_EXTRACTION_PROMPT = """You are a pharmaceutical safety data extraction specialist.

Extract the following structured facts from this safety report. For any field NOT mentioned or unclear, write "Not stated" — NEVER guess.

## Fields to extract:

### Patient
- patient_age: Age (e.g., "45 years", "elderly", "pediatric")
- patient_sex: Sex (Male/Female/Not stated)
- patient_weight: Weight with units
- patient_height: Height with units
- patient_history: Relevant medical history

### Reporter
- reporter_name: Name of person who reported
- reporter_role: Their role (physician, pharmacist, patient, nurse, etc.)
- reporter_country: Country

### Product (Suspect Drug)
- product_name: Drug name (brand or generic)
- product_dose: Dosage (e.g., "50mg twice daily")
- product_route: Route of administration (oral, IV, topical, etc.)
- product_start_date: When the patient started taking the drug
- product_stop_date: When the patient stopped (or "Ongoing")

### Reaction (Adverse Event)
- reaction_description: What happened to the patient
- reaction_onset_date: When symptoms started
- reaction_outcome: Outcome (recovered, recovering, not recovered, fatal, unknown)

### Severity
- is_serious: "Yes" or "No" or "Unknown"
- seriousness_criteria: If serious, why? (death, hospitalization, life-threatening, disability, congenital anomaly, other medically important)

### Narrative
- ai_narrative: Write a 3-5 sentence plain-language case summary.

## Confidence & Source Traceability:
For EVERY extracted field, also provide:
1. A confidence score (0.0 to 1.0) in `field_confidence`
2. Where the fact came from in `source_references` — specify "email_body", "attachment_page_X", or "attachment_filename"

## Output Format (strict JSON):
```json
{{
  "patient_age": "45 years",
  "patient_sex": "Male",
  "patient_weight": "Not stated",
  "patient_height": "Not stated",
  "patient_history": "Hypertension, Type 2 diabetes",
  "reporter_name": "Dr. Jane Smith",
  "reporter_role": "Physician",
  "reporter_country": "United States",
  "product_name": "Cardiomax 50mg",
  "product_dose": "50mg once daily",
  "product_route": "Oral",
  "product_start_date": "2024-01-15",
  "product_stop_date": "2024-02-20",
  "reaction_description": "Patient developed severe cardiac arrhythmia",
  "reaction_onset_date": "2024-02-15",
  "reaction_outcome": "Recovered",
  "is_serious": "Yes",
  "seriousness_criteria": "Hospitalization",
  "ai_narrative": "A 45-year-old male with a history of hypertension began taking Cardiomax 50mg daily on January 15, 2024. Approximately one month later, he developed severe cardiac arrhythmia requiring hospitalization. The drug was discontinued on February 20, and the patient subsequently recovered.",
  "field_confidence": {{
    "patient_age": 0.95,
    "patient_sex": 0.90,
    "product_name": 0.98
  }},
  "source_references": {{
    "patient_age": {{"source": "email_body", "location": "paragraph 1"}},
    "product_name": {{"source": "attachment", "filename": "report.pdf", "page": 1}}
  }}
}}
```

## Document to extract from:

**Subject:** {subject}
**Sender:** {sender}
**Email Body:**
{body_text}

**Attachment Text (if any):**
{attachment_text}
"""

PQC_EXTRACTION_PROMPT = """You are a product quality complaint data extraction specialist.

Extract product quality complaint details from this document. For any field NOT mentioned, write "Not stated".

## Fields to extract:
- product_name: Name of the product with the quality issue
- batch_lot_number: Batch or lot number of the defective product
- complaint_description: What is physically wrong with the product
- photo_mentioned: Was a photo mentioned or attached? ("Yes"/"No"/"Unknown")

## Also provide:
- field_confidence: Confidence score (0.0-1.0) for each field
- source_references: Where each fact was found (email_body / attachment page)

## Output Format (strict JSON):
```json
{{
  "product_name": "Cardiomax 50mg tablets",
  "batch_lot_number": "B2024-789",
  "complaint_description": "Broken seal on the bottle, tablets appear discolored",
  "photo_mentioned": "Yes",
  "field_confidence": {{"product_name": 0.95, "batch_lot_number": 0.90}},
  "source_references": {{"product_name": {{"source": "email_body"}}}}
}}
```

## Document:

**Subject:** {subject}
**Sender:** {sender}
**Body:**
{body_text}

**Attachment Text (if any):**
{attachment_text}
"""

MI_EXTRACTION_PROMPT = """You are a medical information request extraction specialist.

Extract the questions and product/topic information from this medical information request. For any field NOT mentioned, write "Not stated".

## Fields to extract:
- questions_asked: Array of specific questions being asked
- product_topic: What product or topic the questions are about

## Also provide:
- field_confidence: Confidence score (0.0-1.0) for each field
- source_references: Where each fact was found

## Output Format (strict JSON):
```json
{{
  "questions_asked": ["What is the recommended dosage for patients with renal impairment?", "Can this drug be taken with warfarin?"],
  "product_topic": "Cardiomax 50mg - dosing in renal impairment",
  "field_confidence": {{"questions_asked": 0.95, "product_topic": 0.90}},
  "source_references": {{"questions_asked": {{"source": "email_body"}}}}
}}
```

## Document:

**Subject:** {subject}
**Sender:** {sender}
**Body:**
{body_text}

**Attachment Text (if any):**
{attachment_text}
"""

SUMMARY_PROMPT = """Write a concise summary (10-15 sentences) of this document for a human reviewer at a pharmaceutical safety department.

Your summary should:
1. State what type of document this is (email, report form, article, etc.)
2. Summarize the key content
3. State whether it appears relevant to patient safety, product quality, or medical information
4. Note any concerns or items that need human attention
5. Mention the language if it's not in English

## Document:

**Subject:** {subject}
**Sender:** {sender}
**Body:**
{body_text}

**Attachment Text (if any):**
{attachment_text}

Write the summary as a single block of text (10-15 sentences). Do NOT use JSON format for this response.
"""

IMAGE_DESCRIPTION_PROMPT = """Describe this image in the context of a pharmaceutical safety / product quality review.

If the image shows:
- A damaged product → describe the damage (broken seal, discoloration, foreign object, etc.)
- A medical condition (rash, swelling, etc.) → describe what you see
- A form or document → describe what type of form it is and key visible information
- A checkbox form → list which boxes are checked
- Something else → describe it briefly

Also state whether this image should be flagged for human review (Yes/No) and why.

Output as JSON:
```json
{{
  "description": "Photo shows a blister pack with two discolored tablets...",
  "flag_for_review": true,
  "flag_reason": "Possible product quality issue — discolored tablets"
}}
```
"""

PDF_TYPE_DETECTION_PROMPT = """Analyze this text extracted from a PDF and determine its type:

1. **DIGITAL** — A standard digital PDF (report form, letter, structured document)
2. **SCANNED** — A scanned or photographed document (OCR artifacts, poor formatting)
3. **ARTICLE** — A published scientific/medical article (has abstract, methods, references sections)
4. **NON_ENGLISH** — Primary content is in a language other than English

Also detect the language of the content.

Output as JSON:
```json
{{
  "pdf_type": "ARTICLE",
  "detected_language": "English",
  "confidence": 0.92,
  "reasoning": "Contains abstract, introduction, methods, results sections typical of a medical journal article."
}}
```

## Text to analyze (first 2000 chars):
{text_sample}
"""

LITERATURE_SCREENING_PROMPT = """You are screening a published medical/scientific article for patient safety case reports.

Determine:
1. Does this article describe one or more real, identifiable patient cases with adverse drug reactions?
2. If yes, how many distinct cases are described?
3. For each case, extract a brief summary and determine if it's reportable as a safety case.

A case is reportable if it describes:
- A specific (even if anonymized) patient
- A specific drug/product
- A specific adverse reaction/outcome
- Enough detail to file a safety report

## Output Format (strict JSON):
```json
{{
  "contains_cases": true,
  "total_cases": 2,
  "cases": [
    {{
      "case_number": 1,
      "is_reportable": "Yes",
      "patient_identifiable": "Yes",
      "confidence_score": 0.88,
      "case_summary": "A 55-year-old female developed hepatotoxicity after 3 months of Liverplex therapy...",
      "relevance_reason": "Describes a specific patient with identifiable adverse reaction to a named drug.",
      "source_location": "Results section, paragraph 2, page 4"
    }}
  ]
}}
```

## Article text:
{article_text}
"""

TRANSLATION_PROMPT = """Translate the following text from {source_language} to English.
Maintain the original structure and meaning as closely as possible.
If you encounter medical/pharmaceutical terminology, use the standard English medical terms.

## Original text:
{text}

Provide your response as JSON:
```json
{{
  "translated_text": "...",
  "source_language": "{source_language}",
  "translation_confidence": 0.95,
  "notes": "Any translation notes or ambiguities"
}}
```
"""

HANDWRITING_OCR_PROMPT = """This is an image of a handwritten or hand-filled medical/pharmaceutical form.

Please read and extract ALL visible text from this image, including:
1. Printed form labels and fields
2. Handwritten entries in the fields
3. Checked/unchecked checkboxes (indicate [X] for checked, [ ] for unchecked)
4. Any dates, signatures, or stamps

Maintain the form structure as much as possible. If text is illegible, write "[illegible]".

Provide your response as JSON:
```json
{{
  "extracted_text": "Full text extracted from the form...",
  "confidence": 0.75,
  "illegible_sections": ["field name or location where text was not readable"],
  "form_type": "Adverse Event Report Form"
}}
```
"""
