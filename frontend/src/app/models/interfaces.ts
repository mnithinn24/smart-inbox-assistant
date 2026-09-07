/* Interfaces for Smart Inbox Assistant */

export interface EmailListItem {
  message_id: number;
  sender: string | null;
  subject: string | null;
  received_date: string | null;
  processing_status: string;
  attachment_count: number;
  categories: string[];
  max_confidence: number | null;
}

export interface AttachmentResponse {
  attachment_id: number;
  message_id: number;
  filename: string | null;
  content_type: string | null;
  file_size: number | null;
  pdf_type: string | null;
  detected_language: string | null;
  ocr_confidence: number | null;
  extracted_text: string | null;
  translated_text: string | null;
  ai_summary: string | null;
  table_data: any;
  image_descriptions: any;
  processing_time_ms: number | null;
}

export interface EmailMessageResponse {
  message_id: number;
  email_uid: string | null;
  sender: string | null;
  subject: string | null;
  received_date: string | null;
  body_text: string | null;
  processing_status: string;
  error_message: string | null;
  processing_time_ms: number | null;
  created_at: string | null;
  attachments: AttachmentResponse[];
}

export interface Classification {
  classification_id: number;
  category: string;
  confidence_score: number;
  ai_reason: string | null;
  reviewer_action: string;
  reviewer_override: string | null;
  reviewer_notes: string | null;
  reviewed_by: string | null;
  reviewed_at: string | null;
}

export interface ReviewQueueItem {
  message_id: number;
  sender: string | null;
  subject: string | null;
  received_date: string | null;
  body_text_preview: string | null;
  processing_status: string;
  processing_time_ms: number | null;
  attachment_count: number;
  classifications: Classification[];
  ai_summary: string | null;
}

export interface ReviewStats {
  total_messages: number;
  pending_review: number;
  accepted: number;
  overridden: number;
  by_category: { [key: string]: number };
  avg_processing_time_ms: number | null;
  avg_confidence: number | null;
}

export interface ICSRExtraction {
  extraction_id: number;
  message_id: number;
  patient_age: string;
  patient_sex: string;
  patient_weight: string;
  patient_height: string;
  patient_history: string;
  reporter_name: string;
  reporter_role: string;
  reporter_country: string;
  product_name: string;
  product_dose: string;
  product_route: string;
  product_start_date: string;
  product_stop_date: string;
  reaction_description: string;
  reaction_onset_date: string;
  reaction_outcome: string;
  is_serious: string;
  seriousness_criteria: string;
  ai_narrative: string;
  field_confidence: { [key: string]: number };
  source_references: { [key: string]: any };
}

export interface PQCExtraction {
  extraction_id: number;
  message_id: number;
  product_name: string;
  batch_lot_number: string;
  complaint_description: string;
  photo_mentioned: string;
  source_references: { [key: string]: any };
  field_confidence: { [key: string]: number };
}

export interface MIExtraction {
  extraction_id: number;
  message_id: number;
  questions_asked: string[];
  product_topic: string;
  source_references: { [key: string]: any };
  field_confidence: { [key: string]: number };
}

export interface ExtractionSummary {
  message_id: number;
  categories: string[];
  icsr: ICSRExtraction | null;
  pqc: PQCExtraction | null;
  mi: MIExtraction | null;
}

export interface AuditLogEntry {
  log_id: number;
  message_id: number | null;
  action_type: string;
  action_detail: any;
  performed_by: string | null;
  timestamp: string | null;
}

export interface LiteratureArticle {
  article_id: number;
  filename: string;
  processing_status: string;
  processing_time_ms: number | null;
  upload_timestamp: string;
  cases_found: number;
}

export interface LiteratureCase {
  case_id: number;
  case_number: number;
  is_reportable: string;
  relevance_reason: string | null;
  case_summary: string | null;
  patient_identifiable: string;
  confidence_score: number;
  source_location: string | null;
}
