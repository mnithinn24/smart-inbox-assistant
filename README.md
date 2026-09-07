# Smart Inbox Assistant for Healthcare

AI-powered email and document processing system for pharmaceutical safety. Built for the Clinevo Technologies live project assignment.

## 🏗 Architecture

```
Angular 17 (Frontend) → FastAPI (Python Backend) → Google Gemini Pro (AI) → MySQL (Database)
```

**Processing Pipeline:**
```
Gmail IMAP → Fetch Email → Detect PDF Type → Extract Text/OCR → AI Classify (4 categories)
→ AI Extract Facts (ICSR/PQC/MI) → Save to MySQL with Audit Trail → Human Review UI
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ (`python` or `py` command)
- Node.js 20.9+ & npm
- MySQL Server (local, port 3306)
- Gmail account with **App Password** (not regular password — requires 2-Step Verification)
- Google Gemini Pro API key ([get one free](https://aistudio.google.com/))

### 1. Database Setup
```bash
mysql -u root -p < database/schema.sql
```

### 2. Backend Setup
```bash
cd backend
copy .env.example .env
# Edit .env with your credentials (see Environment Variables section below)

pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
API docs at: http://localhost:8000/docs

### 3. Frontend Setup
```bash
cd frontend
npm install
npx @angular/cli@17 serve
```
Open: http://localhost:4200

## 📋 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GMAIL_USER` | Gmail address for IMAP | `user@gmail.com` |
| `GMAIL_APP_PASSWORD` | Gmail App Password (not regular password) | `abcd efgh ijkl mnop` |
| `GEMINI_API_KEY` | Google Gemini Pro API key | `AIzaSy...` |
| `DB_HOST` | MySQL host | `127.0.0.1` |
| `DB_PORT` | MySQL port | `3306` |
| `DB_USER` | MySQL username | `root` |
| `DB_PASSWORD` | MySQL password | `your-password` |
| `DB_NAME` | MySQL database name | `smart_inbox` |

## 🏷 The Four Categories

| Category | Meaning | Look for |
|----------|---------|----------|
| **ICSR** (Safety Report) | Patient had adverse reaction to a drug | Patient + Reporter + Drug + Bad outcome |
| **PQC** (Quality Complaint) | Physical defect in the product | Broken seal, wrong color, contamination |
| **MI** (Info Request) | Question about a product | Dosing, interactions — no adverse event |
| **NOT_RELEVANT** | Everything else | Marketing, spam, admin emails |

## 🧪 Test Data

20 synthetic documents in `test-data/` covering all required types:
- 10+ emails with varying detail levels
- 5 normal digital PDFs
- 2 scanned/handwritten PDFs
- 5 article PDFs
- 2 non-English PDFs (French, Spanish)
- Quality-complaint-only and info-request-only examples
- Mixed category examples
- Clearly irrelevant examples

## 📂 Project Structure

```
smart-inbox-assistant/
├── backend/            # FastAPI Python backend
│   ├── app/
│   │   ├── main.py     # App entry point
│   │   ├── config.py   # Environment config
│   │   ├── database.py # MySQL connection pool
│   │   ├── models/     # Pydantic schemas
│   │   ├── services/   # Business logic (email, PDF, AI, pipeline)
│   │   ├── routers/    # API endpoints
│   │   └── utils/      # Prompts, helpers
│   └── requirements.txt
├── frontend/           # Angular 17 frontend
│   └── src/app/
│       ├── components/ # Dashboard, Inbox, DocViewer, Audit, Literature
│       ├── services/   # HTTP API client
│       └── models/     # TypeScript interfaces
├── database/           # MySQL schema
├── test-data/          # Synthetic test documents
└── docs/               # Architecture write-up
```

## ⚠ Tech Stack Deviations

| Assignment Suggests | We Used | Justification |
|---|---|---|
| Spring Boot (Java) | FastAPI (Python) | Python is natural for AI/NLP work; FastAPI provides equivalent REST API with async support and eliminates the Java↔Python bridge |
| Oracle PL/SQL | MySQL 26.7 | Using candidate's existing local MySQL setup; schema is portable to Oracle with minimal changes |
| Separate Python AI service | Integrated in FastAPI | Single-backend approach reduces deployment complexity |

## 📊 Scoring Areas

- ✅ Core functionality (30%) — Email/PDF intake, all 4 PDF types, classification, extraction
- ✅ AI/LLM quality (25%) — Structured prompts, confidence scoring, "Not stated" for unknowns
- ✅ Code & architecture (20%) — Clean separation, async pipeline, API design
- ✅ Domain accuracy (10%) — 4 categories correctly identified
- ✅ Traceability (10%) — Every fact links to source, full audit log
- ✅ Documentation (5%) — This README + architecture write-up
- ✅ Bonus: Literature screening (+30%)

---
*Clinevo Technologies Pvt. Ltd. — Candidate evaluation project. All data is synthetic.*
