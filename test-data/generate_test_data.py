"""
Smart Inbox Assistant — Synthetic Test Data Generator
Generates 20 synthetic email/document samples for testing.
Run: py test-data/generate_test_data.py
"""
import json
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def generate_test_emails():
    """Generate 20 synthetic test emails covering all required types."""
    emails = [
        # ── ICSR (Safety Reports) — 5 emails ──
        {
            "id": 1,
            "type": "ICSR",
            "subject": "Adverse Event Report - Patient John D. on Cardiomax 50mg",
            "sender": "Dr. Sarah Mitchell <sarah.mitchell@hospital-example.com>",
            "body": """Dear Safety Team,

I am writing to report an adverse drug reaction observed in my patient.

Patient Information:
- Name: John D. (initials used for privacy)
- Age: 58 years old
- Sex: Male
- Weight: 82 kg
- Medical History: Hypertension, Type 2 Diabetes

Reporter: Dr. Sarah Mitchell, Cardiologist
Country: United States

Product: Cardiomax 50mg tablets
Dose: 50mg once daily, oral administration
Start Date: January 15, 2024
Stop Date: February 28, 2024 (drug was discontinued)

Adverse Event:
The patient developed severe cardiac arrhythmia approximately 6 weeks after starting Cardiomax. 
Onset date was approximately February 25, 2024. The patient was hospitalized for 3 days.
The arrhythmia resolved after discontinuation of Cardiomax.

Outcome: Recovered
Seriousness: Yes — required hospitalization

Please process this report accordingly.

Best regards,
Dr. Sarah Mitchell
Cardiology Department""",
            "has_pdf": False,
            "expected_fields": {
                "patient_age": "58 years",
                "patient_sex": "Male",
                "product_name": "Cardiomax 50mg",
                "is_serious": "Yes"
            }
        },
        {
            "id": 2,
            "type": "ICSR",
            "subject": "RE: Skin Rash - Possible Reaction to DermaClear Cream",
            "sender": "pharmacy.reports@rx-example.com",
            "body": """A 32-year-old female patient reported developing a widespread skin rash after using DermaClear Anti-Acne Cream for two weeks. She applied the cream topically twice daily starting March 1st. The rash appeared on March 14th and covered both arms and chest. The patient stopped using the cream. As of our last contact, the rash is still present but improving. Patient has no relevant medical history. Reported by the patient herself at our pharmacy.

This report was forwarded from our branch in Toronto, Canada.""",
            "has_pdf": False
        },
        {
            "id": 3,
            "type": "ICSR",
            "subject": "Fwd: Patient Case - Headaches with Neurova 100mg",
            "sender": "Dr. James Chen <j.chen@neuro-clinic.example.com>",
            "body": """An elderly female patient (approximately 75 years old) has been experiencing persistent severe headaches since starting Neurova 100mg capsules. She takes it orally once at bedtime for neuropathic pain. Treatment started on December 1, 2023. Headaches started around December 20. The drug has NOT been stopped yet. No improvement noted. The patient also takes Lisinopril 10mg for blood pressure.

Reporter: Dr. James Chen, Neurologist, Singapore
This is a non-serious event. Outcome: Not recovered.""",
            "has_pdf": False
        },
        {
            "id": 4,
            "type": "ICSR",
            "subject": "Patient Safety Report — Liver Function Abnormality",
            "sender": "nurse.reporting@hospital-uk.example.com",
            "body": """Reporting a suspected adverse reaction:

A 45-year-old male patient developed elevated liver enzymes (ALT 320 U/L, AST 280 U/L) after 2 months on Hepatoguard 200mg. The patient was taking 200mg twice daily by mouth. Drug was started August 1, 2024 and stopped October 5, 2024 after lab results. The patient was not hospitalized but was closely monitored as an outpatient. Liver function is slowly returning to normal.

Reporter: Nurse Emily Watson, Ward 5, Royal General Hospital, United Kingdom.
Serious? Yes — other medically important condition.""",
            "has_pdf": True,
            "pdf_name": "lab_results_hepatoguard.pdf",
            "pdf_type": "DIGITAL"
        },
        {
            "id": 5,
            "type": "ICSR",
            "subject": "Informe de reacción adversa - Paciente con GastroRelief",
            "sender": "dr.garcia@clinica-madrid.example.com",
            "body": """Estimado equipo de seguridad,

Quiero informar una reacción adversa en mi paciente. Un hombre de 60 años desarrolló náuseas severas y vómitos después de tomar GastroRelief 30mg por vía oral durante una semana. El medicamento fue iniciado el 5 de abril de 2024. Los síntomas comenzaron el 12 de abril. El paciente dejó de tomar el medicamento y se recuperó completamente.

Reportado por: Dr. García, Gastroenterólogo, Madrid, España.
No es un evento grave.""",
            "has_pdf": False,
            "expected_language": "Spanish"
        },
        # ── PQC (Product Quality Complaints) — 3 emails ──
        {
            "id": 6,
            "type": "PQC",
            "subject": "Defective Product - Broken Seal on Cardiomax Bottle",
            "sender": "complaints@pharma-dist.example.com",
            "body": """We received a complaint from a retail pharmacy regarding Cardiomax 50mg tablets.

Product: Cardiomax 50mg tablets, 30-count bottle
Batch/Lot Number: B2024-4567
Issue: The tamper-evident seal on the bottle was broken when received. The bottle cap was loose and two tablets appeared to have a different color (yellowish instead of white).

A photo has been taken and is attached to this email.

Please investigate this quality issue urgently.

Reported by: PharmaCare Distribution Center""",
            "has_pdf": False
        },
        {
            "id": 7,
            "type": "PQC",
            "subject": "Foreign Particle Found in DermaClear Cream Tube",
            "sender": "quality.reports@consumer-feedback.example.com",
            "body": """A consumer reported finding a small metallic foreign particle inside their tube of DermaClear Anti-Acne Cream (50g tube). The consumer noticed the particle when squeezing cream onto their finger.

Product: DermaClear Anti-Acne Cream, 50g tube
Lot Number: DC-2024-089
Manufacturing Site: Plant B

The consumer has retained the tube and particle. No injury was reported. No photos were taken.""",
            "has_pdf": False
        },
        {
            "id": 8,
            "type": "PQC",
            "subject": "Packaging Error - Wrong Label on Neurova Shipment",
            "sender": "logistics@hospital-supply.example.com",
            "body": """We received a shipment of Neurova 100mg capsules but the outer packaging label indicates Neurova 50mg. The blister packs inside correctly say 100mg. This labeling discrepancy needs to be investigated.

Batch: NV-2024-312
Quantity affected: 500 boxes
No patient impact as the error was caught during receiving inspection.""",
            "has_pdf": True,
            "pdf_name": "shipment_photos.pdf",
            "pdf_type": "SCANNED"
        },
        # ── MI (Medical Information Requests) — 3 emails ──
        {
            "id": 9,
            "type": "MI",
            "subject": "Dosing Question - Cardiomax in Renal Impairment",
            "sender": "dr.patel@kidney-center.example.com",
            "body": """Dear Medical Information Team,

I have a patient with moderate renal impairment (CrCl 35 mL/min) who needs to start Cardiomax. 

My questions:
1. Is dose adjustment required for patients with renal impairment?
2. What is the recommended starting dose for CrCl 30-50 mL/min?
3. Are there any specific monitoring parameters I should follow?

Thank you for your assistance.

Dr. Anjali Patel
Nephrology, Mumbai, India""",
            "has_pdf": False
        },
        {
            "id": 10,
            "type": "MI",
            "subject": "Drug Interaction Inquiry - Neurova + Warfarin",
            "sender": "pharmacist@community-rx.example.com",
            "body": """Hello,

A patient of ours is currently on Warfarin for atrial fibrillation and their neurologist wants to start them on Neurova 100mg.

Can you please provide information on:
- Any known drug interactions between Neurova and Warfarin?
- Should INR monitoring frequency be increased?

Thanks,
Michael Torres, PharmD
Community Pharmacy""",
            "has_pdf": False
        },
        {
            "id": 11,
            "type": "MI",
            "subject": "Request for Product Information - Hepatoguard",
            "sender": "medical.affairs@partner-hospital.example.com",
            "body": """We are considering adding Hepatoguard to our hospital formulary. Could you please send us:

1. The full prescribing information / product monograph
2. Any available clinical trial data
3. Storage requirements and shelf life information

Our formulary committee meets next month. Thank you.""",
            "has_pdf": False
        },
        # ── NOT_RELEVANT — 4 emails ──
        {
            "id": 12,
            "type": "NOT_RELEVANT",
            "subject": "Annual Company Picnic - Save the Date!",
            "sender": "hr@company-internal.example.com",
            "body": """Hi everyone!

Save the date for our annual company picnic! It will be held on Saturday, July 15th at Riverside Park. Food, games, and fun for the whole family!

RSVP by July 1st. See you there!

Best,
HR Team"""
        },
        {
            "id": 13,
            "type": "NOT_RELEVANT",
            "subject": "Invoice #INV-2024-789 - Office Supplies",
            "sender": "billing@officesupply.example.com",
            "body": """Dear Accounts Payable,

Please find attached invoice #INV-2024-789 for office supplies delivered on March 15, 2024.

Total Amount: $1,245.67
Payment Terms: Net 30

Thank you for your business."""
        },
        {
            "id": 14,
            "type": "NOT_RELEVANT",
            "subject": "Newsletter - Pharma Industry Update Q1 2024",
            "sender": "newsletter@pharma-news.example.com",
            "body": """Welcome to our quarterly pharma industry update!

In this edition:
- FDA approves 12 new drugs in Q1 2024
- European regulatory changes overview
- Upcoming conferences and events
- Market trends and analysis

This is a marketing email. To unsubscribe, click here."""
        },
        {
            "id": 15,
            "type": "NOT_RELEVANT",
            "subject": "IT Maintenance - Server Downtime This Weekend",
            "sender": "it-support@company-internal.example.com",
            "body": """Dear all,

Planned maintenance will occur this Saturday from 2 AM to 6 AM EST. Email and internal systems may be briefly unavailable. Please save your work before Friday EOD.

IT Infrastructure Team"""
        },
        # ── MIXED/DUAL CATEGORY — 2 emails ──
        {
            "id": 16,
            "type": "ICSR+PQC",
            "subject": "Defective Inhaler Caused Breathing Difficulty",
            "sender": "er.report@hospital-example.com",
            "body": """Emergency department report:

A 28-year-old female asthma patient presented to the ER with acute breathing difficulty. She reported that her BreathEasy 200mcg inhaler (Lot: BE-2024-456) malfunctioned — the actuator was stuck and did not deliver medication when pressed. As a result, her asthma attack was not controlled, and she required emergency nebulizer treatment and overnight observation.

The defective inhaler has been retained. The patient recovered after treatment.

This appears to be BOTH a product quality issue (defective actuator) AND a patient safety case (hospitalization due to failure to deliver medication).

Reported by ER attending Dr. Amanda Lee, City General Hospital, Australia.""",
            "has_pdf": False
        },
        {
            "id": 17,
            "type": "ICSR+MI",
            "subject": "Patient Reaction and Dosage Question - GastroRelief",
            "sender": "dr.kim@gi-clinic.example.com",
            "body": """Hello,

I have a patient (42M) who developed mild diarrhea after starting GastroRelief 30mg once daily. The diarrhea started about 3 days after starting the medication. The patient is continuing the medication.

Also, I wanted to ask: can the dose be split into 15mg twice daily instead of 30mg once daily? Would this potentially reduce GI side effects?

Thank you,
Dr. Kim, Seoul, South Korea""",
            "has_pdf": False
        },
        # ── SPECIAL PDF TYPES ──
        {
            "id": 18,
            "type": "ICSR",
            "subject": "Scanned Adverse Event Form - Handwritten Report",
            "sender": "medical.records@rural-clinic.example.com",
            "body": """Please find attached the handwritten adverse event report form from our rural clinic. The form was filled out by the attending physician Dr. Tanaka.

The attached PDF is a scan of the paper form.""",
            "has_pdf": True,
            "pdf_name": "handwritten_ae_form.pdf",
            "pdf_type": "SCANNED"
        },
        {
            "id": 19,
            "type": "ICSR",
            "subject": "Published Case Report - Hepatotoxicity with Hepatoguard",
            "sender": "literature.monitoring@example.com",
            "body": """The following published article was identified during routine literature screening. It contains a case report that may require safety assessment.

Article attached.""",
            "has_pdf": True,
            "pdf_name": "journal_article_hepatoguard_case.pdf",
            "pdf_type": "ARTICLE"
        },
        {
            "id": 20,
            "type": "ICSR",
            "subject": "Rapport d'effet indésirable - Patient sous Neurova",
            "sender": "pharmacovigilance@hopital-paris.example.com",
            "body": """Cher service de pharmacovigilance,

Nous souhaitons signaler un effet indésirable grave chez un patient de 55 ans traité par Neurova 100mg.

Le patient a développé des vertiges sévères et une vision floue après deux semaines de traitement. Le médicament a été arrêté et les symptômes se sont améliorés progressivement. Le patient a été hospitalisé pendant deux jours pour observation.

Déclarant: Dr. Dupont, Neurologue, Hôpital Saint-Michel, Paris, France
Gravité: Oui - hospitalisation nécessaire

Cordialement,
Service de Pharmacovigilance""",
            "has_pdf": True,
            "pdf_name": "rapport_neurova_fr.pdf",
            "pdf_type": "NON_ENGLISH",
            "expected_language": "French"
        }
    ]

    # Write all test emails to JSON
    output_file = os.path.join(OUTPUT_DIR, "test_emails.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(emails, f, indent=2, ensure_ascii=False)
    print(f"Generated {len(emails)} test emails -> {output_file}")

    # Also write a summary
    summary_file = os.path.join(OUTPUT_DIR, "test_data_summary.md")
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write("# Test Data Summary\n\n")
        f.write(f"**Total test documents: {len(emails)}**\n\n")
        f.write("| # | Type | Subject | Has PDF | PDF Type | Language |\n")
        f.write("|---|------|---------|---------|----------|----------|\n")
        for e in emails:
            pdf_type = e.get("pdf_type", "—")
            lang = e.get("expected_language", "English")
            has_pdf = "✓" if e.get("has_pdf") else "—"
            f.write(f"| {e['id']} | {e['type']} | {e['subject'][:50]}... | {has_pdf} | {pdf_type} | {lang} |\n")

        f.write("\n## Category Distribution\n\n")
        cats = {}
        for e in emails:
            for cat in e["type"].split("+"):
                cats[cat] = cats.get(cat, 0) + 1
        for cat, count in sorted(cats.items()):
            f.write(f"- **{cat}**: {count}\n")

        f.write("\n## PDF Types\n\n")
        pdf_types = {}
        for e in emails:
            if e.get("has_pdf"):
                pt = e.get("pdf_type", "DIGITAL")
                pdf_types[pt] = pdf_types.get(pt, 0) + 1
        for pt, count in sorted(pdf_types.items()):
            f.write(f"- **{pt}**: {count}\n")

    print(f"Generated summary -> {summary_file}")


if __name__ == "__main__":
    generate_test_emails()
