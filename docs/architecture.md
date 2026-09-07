# Smart Inbox Assistant — Architecture Write-Up

## 1. System Overview

The Smart Inbox Assistant automates the initial triage of incoming pharmaceutical safety communications. It reads emails and PDF attachments, uses Google Gemini Pro to classify and extract structured data, and presents everything to a human reviewer through a web interface.

```
┌──────────────┐     ┌──────────────────────────────┐     ┌───────────┐
│  Gmail IMAP  │────►│     FastAPI Backend           │────►│  MySQL    │
│  (Incoming)  │     │  ┌─────────┐  ┌──────────┐   │     │  Database │
└──────────────┘     │  │ Email   │  │ PDF      │   │     └───────────┘
                     │  │ Service │  │ Service  │   │
┌──────────────┐     │  └────┬────┘  └────┬─────┘   │     ┌───────────┐
│  PDF Upload  │────►│       │            │         │────►│  Angular  │
│  (Direct)    │     │  ┌────▼────────────▼─────┐   │     │  Frontend │
└──────────────┘     │  │   Processing Pipeline  │   │     └───────────┘
                     │  │   (asyncio Queue)      │   │
                     │  └────────┬───────────────┘   │
                     │           │                   │
                     │  ┌────────▼───────────────┐   │
                     │  │  Gemini Pro AI Service  │   │
                     │  │  (Classify + Extract)   │   │
                     │  └────────────────────────┘   │
                     └──────────────────────────────┘
```

## 2. Technology Choices

### Backend: FastAPI (Python)
- **Why Python**: Natural choice for AI/NLP work. Direct access to `google-generativeai` SDK, PDF processing libraries (`PyPDF2`, `Pillow`), and language detection (`langdetect`).
- **Why FastAPI**: Async-native (critical for non-blocking I/O with IMAP, database, and AI API calls), automatic Swagger/OpenAPI docs, and Pydantic validation.
- **Deviation from assignment**: Assignment suggests Spring Boot (Java). Python eliminates the need for a separate AI microservice and simplifies the stack.

### Frontend: Angular 17
- **Why Angular**: Enterprise-grade framework suitable for a healthcare review dashboard. Strong typing with TypeScript matches the structured data model.
- **Standalone components**: Using Angular 17's standalone component architecture for simpler imports and tree-shaking.

### Database: MySQL 26.7
- **Why MySQL**: Candidate's existing local setup. Schema is normalized (9 tables) and portable to Oracle/PostgreSQL.
- **Deviation**: Assignment suggests Oracle PL/SQL. Schema uses standard SQL and would work with minimal changes.

### AI: Google Gemini Pro
- **Model**: `gemini-2.0-flash` for fast inference.
- **Capabilities used**: Text understanding, classification, structured JSON output, vision (for scanned PDFs), translation.

## 3. Database Schema

### 9 Tables:
1. **inbox_messages** — Core email records with processing status
2. **attachments** — PDF/file metadata, extracted text, OCR results
3. **classifications** — AI category assignments with confidence + reviewer actions
4. **icsr_extractions** — Safety report structured facts (20+ fields)
5. **pqc_extractions** — Quality complaint structured facts
6. **mi_extractions** — Medical info request structured facts
7. **audit_log** — Complete trail of every AI decision and human action
8. **literature_articles** — Uploaded articles for literature screening (bonus)
9. **literature_cases** — Identified cases from articles (bonus)

### Key Design Decisions:
- **Separate extraction tables per category** (not a single polymorphic table) — matches the very different field sets for ICSR vs PQC vs MI.
- **JSON columns** for `field_confidence` and `source_references` — flexible per-field metadata without additional join tables.
- **Audit log captures snapshots** — `input_snapshot` and `output_snapshot` record what went in and came out, enabling debugging.

## 4. Processing Pipeline

### Step-by-step flow for each message:

```
1. FETCH        Email fetched from Gmail IMAP → saved to inbox_messages + attachments
2. QUEUE        Message ID added to asyncio.Queue → background worker picks it up
3. PDF PROCESS  For each PDF attachment:
                  a. Extract text (PyPDF2)
                  b. Detect type (digital/scanned/article/non-English)
                  c. If scanned → Gemini Vision OCR
                  d. If non-English → Gemini translation
                  e. Extract tables and images
                  f. Generate per-attachment AI summary
4. CLASSIFY     Combined email + attachment text → Gemini classification prompt
                  → Returns 1+ categories with confidence scores
                  → Each category saved to classifications table
5. EXTRACT      For each assigned category:
                  - ICSR → 20+ structured fields (patient, reporter, product, reaction)
                  - PQC → product, batch, complaint description, photo
                  - MI → questions asked, product/topic
                  Each field gets confidence score + source reference
6. STATUS       Message marked COMPLETED with total processing time
7. AUDIT        Every step logged with timestamps, AI model, input/output snapshots
```

### Error Handling:
- Pipeline catches exceptions at each stage
- On failure: message marked as ERROR with error_message
- Individual attachment failures don't block the rest of the pipeline
- All errors logged to audit trail

## 5. AI Prompting Strategy

### Classification Prompt Design:
- **Multi-label**: A message CAN have multiple categories (e.g., defective product that caused adverse reaction = ICSR + PQC).
- **Structured output**: Forces JSON format with `classifications` array.
- **Confidence scores**: 0.0-1.0 for each category.
- **Reasoning**: AI must provide one-line reason per category.

### Extraction Prompt Design:
- **"Not stated" rule**: AI must write "Not stated" for any missing field — never guess.
- **Field-level confidence**: Each extracted field gets its own confidence score.
- **Source traceability**: Each fact links back to "email_body" or "attachment_page_X".
- **Double-curly-brace escaping**: Python `.format()` compatibility in prompts containing JSON examples.

### PDF Type Handling:
| Type | Detection | Processing |
|------|-----------|------------|
| DIGITAL | Text > 100 chars | Direct text extraction |
| SCANNED | Text < 100 chars | Gemini Vision OCR on page images |
| ARTICLE | Contains "abstract", "methods", etc. (4+ indicators) | Literature screening pipeline |
| NON_ENGLISH | Language detection ≠ English | Gemini translation → then standard processing |

## 6. Frontend Architecture

### Pages:
1. **Dashboard** — Stats grid (total, pending, accepted, overridden), category breakdown, performance metrics, fetch button
2. **Inbox Queue** — Filterable table with categories, confidence bars, review status
3. **Document Viewer** — Split-pane: left shows original content (email + PDFs), right shows AI results (classification + extraction + audit trail)
4. **Audit Log** — Paginated, filterable trail of all actions
5. **Literature** (bonus) — Drag-and-drop upload, article processing, case identification

### Human Review Controls:
- **Accept**: Reviewer agrees with AI classification
- **Override**: Reviewer changes the category with notes
- Both actions logged to audit trail with reviewer identity

## 7. Security & Privacy Considerations

- **No real patient data**: All test data is synthetic
- **Credentials in .env**: Not committed to version control
- **Gmail App Password**: Uses Google's App Password (not the main password)
- **CORS restricted**: Only localhost:4200 allowed

## 8. Traceability

Every AI decision is traceable through three mechanisms:
1. **Field-level confidence scores** — Know how certain the AI was about each extracted fact
2. **Source references** — Know exactly where each fact came from (email body vs attachment page N)
3. **Audit log** — Complete timeline of AI classifications, extractions, and human reviews with input/output snapshots

## 9. Bonus: Literature Screening

The literature screening module screens published medical articles for reportable patient safety cases:
1. Upload article PDFs (batch upload supported)
2. Extract text from PDF
3. AI screens for patient cases with specific criteria:
   - Identifiable patient
   - Specific drug/product
   - Adverse reaction/outcome
   - Enough detail for a safety report
4. Each identified case gets: case summary, reportability assessment, confidence score, source location

## 10. Testing Approach

### 20 Synthetic Test Documents:
- 7 ICSR (safety reports) — varying detail levels, languages (English, Spanish, French)
- 3 PQC (quality complaints) — broken seal, foreign particle, labeling error
- 3 MI (info requests) — dosing, interactions, formulary
- 4 NOT_RELEVANT — picnic invite, invoice, newsletter, IT maintenance
- 2 Mixed category — ICSR+PQC (defective inhaler causing ER visit), ICSR+MI (reaction + dosing question)
- 1 Scanned/handwritten PDF
- 1 Article PDF
- 1 Non-English (French) PDF

### Verification:
- Backend: FastAPI auto-generated Swagger UI at /docs for API testing
- Frontend: Manual verification of all pages and flows
- Pipeline: Load test data → process → verify classifications and extractions in UI
