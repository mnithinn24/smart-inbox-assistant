import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { EmailMessageResponse, ExtractionSummary, Classification, AuditLogEntry } from '../../models/interfaces';

@Component({
  selector: 'app-document-viewer',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  template: `
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px;">
      <a routerLink="/inbox" class="btn btn-outline btn-sm">← Back</a>
      <div>
        <h2 style="font-size: 18px;">{{ message?.subject || 'Loading...' }}</h2>
        <p style="color: var(--text-secondary); font-size: 12px;">
          From: {{ message?.sender }} · {{ formatDate(message?.received_date) }}
          <span *ngIf="message?.processing_time_ms" style="margin-left: 12px;">⏱ {{ (message!.processing_time_ms! / 1000).toFixed(1) }}s</span>
        </p>
      </div>
      <button class="btn btn-outline btn-sm" style="margin-left: auto;" (click)="reprocess()" [disabled]="reprocessing">
        {{ reprocessing ? '⟳ Processing...' : '🔄 Reprocess' }}
      </button>
    </div>

    <!-- Notification -->
    <div *ngIf="notification" class="card animate-in" style="margin-bottom: 12px; padding: 10px 16px; border-color: rgba(16,185,129,0.3);">
      <span style="color: var(--color-success);">✓</span> {{ notification }}
    </div>

    <!-- Split Pane -->
    <div class="split-pane" *ngIf="message">
      <!-- LEFT: Original Content -->
      <div class="split-pane-left">
        <!-- Email Body -->
        <div class="card" style="margin-bottom: 16px;">
          <div class="card-header"><span class="card-title">📧 Email Body</span></div>
          <pre style="white-space: pre-wrap; font-family: inherit; font-size: 13px; color: var(--text-secondary); max-height: 300px; overflow-y: auto;">{{ message.body_text || 'No body text' }}</pre>
        </div>

        <!-- Attachments -->
        <div *ngFor="let att of message.attachments" class="card" style="margin-bottom: 16px;">
          <div class="card-header">
            <span class="card-title">📎 {{ att.filename }}</span>
            <span *ngIf="att.pdf_type" [class]="'badge badge-' + (att.pdf_type === 'SCANNED' ? 'pqc' : att.pdf_type === 'ARTICLE' ? 'mi' : att.pdf_type === 'NON_ENGLISH' ? 'icsr' : 'completed')">
              {{ att.pdf_type }}
            </span>
          </div>

          <div *ngIf="att.detected_language && att.detected_language !== 'English'" style="margin-bottom: 8px;">
            <span class="badge badge-icsr">🌐 {{ att.detected_language }}</span>
          </div>

          <div *ngIf="att.ocr_confidence !== null" style="margin-bottom: 8px; font-size: 12px; color: var(--text-muted);">
            OCR Confidence: {{ (att.ocr_confidence! * 100).toFixed(0) }}%
          </div>

          <!-- AI Summary -->
          <div *ngIf="att.ai_summary" style="margin-bottom: 12px; padding: 12px; background: rgba(59,130,246,0.05); border-radius: 8px; border-left: 3px solid var(--accent-primary);">
            <div style="font-size: 11px; font-weight: 600; color: var(--accent-primary); margin-bottom: 6px;">AI SUMMARY</div>
            <p style="font-size: 13px; color: var(--text-secondary); line-height: 1.6;">{{ att.ai_summary }}</p>
          </div>

          <!-- Extracted Text Preview -->
          <div *ngIf="att.extracted_text" style="margin-bottom: 12px;">
            <div style="font-size: 11px; font-weight: 600; color: var(--text-muted); margin-bottom: 4px;">EXTRACTED TEXT</div>
            <pre style="white-space: pre-wrap; font-family: inherit; font-size: 12px; color: var(--text-secondary); max-height: 200px; overflow-y: auto; padding: 8px; background: rgba(17,24,39,0.5); border-radius: 6px;">{{ att.extracted_text | slice:0:2000 }}{{ att.extracted_text!.length > 2000 ? '...' : '' }}</pre>
          </div>

          <!-- Tables -->
          <div *ngIf="att.table_data && att.table_data.length > 0" style="margin-bottom: 12px;">
            <div style="font-size: 11px; font-weight: 600; color: var(--text-muted); margin-bottom: 4px;">EXTRACTED TABLES ({{ att.table_data.length }})</div>
            <div *ngFor="let table of att.table_data" style="overflow-x: auto; margin-bottom: 8px;">
              <table class="data-table" style="font-size: 11px;">
                <tbody>
                  <tr *ngFor="let row of table.rows; let i = index" [style.font-weight]="i === 0 ? '600' : '400'">
                    <td *ngFor="let cell of row" style="padding: 6px 8px;">{{ cell }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Image Descriptions -->
          <div *ngIf="att.image_descriptions && att.image_descriptions.length > 0" style="margin-bottom: 12px;">
            <div style="font-size: 11px; font-weight: 600; color: var(--text-muted); margin-bottom: 4px;">IMAGES ({{ att.image_descriptions.length }})</div>
            <div *ngFor="let img of att.image_descriptions" style="padding: 8px; margin-bottom: 4px; background: rgba(17,24,39,0.5); border-radius: 6px;">
              <p style="font-size: 12px;">📷 Page {{ img.page }}: {{ img.description }}</p>
              <span *ngIf="img.flag_for_review" class="badge badge-icsr" style="margin-top: 4px;">⚠ Needs Review: {{ img.flag_reason }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- RIGHT: Classification & Extraction -->
      <div class="split-pane-right">
        <!-- Classifications -->
        <div class="card" style="margin-bottom: 16px;">
          <div class="card-header"><span class="card-title">🏷 AI Classification</span></div>
          <div *ngFor="let clf of classifications" style="padding: 12px; margin-bottom: 8px; background: rgba(17,24,39,0.5); border-radius: 8px; border: 1px solid var(--border-color);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <span [class]="'badge badge-' + clf.category.toLowerCase().replace('_','-')" style="font-size: 13px; padding: 4px 12px;">{{ getCategoryLabel(clf.category) }}</span>
              <div class="confidence-bar">
                <div class="confidence-track" style="max-width: 60px;">
                  <div class="confidence-fill" [class]="getConfClass(clf.confidence_score)" [style.width.%]="clf.confidence_score * 100"></div>
                </div>
                <span class="confidence-label">{{ (clf.confidence_score * 100).toFixed(0) }}%</span>
              </div>
            </div>
            <p style="font-size: 12px; color: var(--text-secondary); margin-bottom: 8px;">{{ clf.ai_reason }}</p>
            <div style="display: flex; gap: 8px; align-items: center;">
              <span [class]="'badge badge-' + clf.reviewer_action.toLowerCase()">{{ clf.reviewer_action }}</span>
              <button *ngIf="clf.reviewer_action === 'PENDING'" class="btn btn-success btn-sm" (click)="accept(clf)">✓ Accept</button>
              <button *ngIf="clf.reviewer_action === 'PENDING'" class="btn btn-warning btn-sm" (click)="showOverride(clf)">✎ Override</button>
              <button *ngIf="clf.reviewer_action === 'PENDING'" class="btn btn-sm" style="background: rgba(239,68,68,0.15); color: #ef4444; border: 1px solid rgba(239,68,68,0.3);" (click)="reject(clf)">✗ Reject</button>
            </div>
            <!-- Override Form -->
            <div *ngIf="overridingId === clf.classification_id" style="margin-top: 10px; padding: 10px; background: rgba(0,0,0,0.2); border-radius: 6px;" class="animate-in">
              <select class="form-select" [(ngModel)]="overrideCategory" style="margin-bottom: 8px;">
                <option value="ICSR">Safety Report (ICSR)</option>
                <option value="PQC">Quality Complaint (PQC)</option>
                <option value="MI">Info Request (MI)</option>
                <option value="NOT_RELEVANT">Not Relevant</option>
              </select>
              <textarea class="form-textarea" [(ngModel)]="overrideNotes" placeholder="Override reason..." style="min-height: 50px; margin-bottom: 8px;"></textarea>
              <div style="display: flex; gap: 8px;">
                <button class="btn btn-warning btn-sm" (click)="submitOverride(clf)">Submit Override</button>
                <button class="btn btn-outline btn-sm" (click)="overridingId = 0">Cancel</button>
              </div>
            </div>
          </div>
          <div *ngIf="classifications.length === 0" class="empty-state" style="padding: 20px;">
            <p>No classifications — message may still be processing.</p>
          </div>
        </div>

        <!-- ICSR Extraction -->
        <div *ngIf="extraction?.icsr" class="card" style="margin-bottom: 16px;">
          <div class="card-header"><span class="card-title">⚠ Safety Report Extraction</span></div>

          <div class="extraction-group">
            <div class="extraction-group-title">Patient</div>
            <div class="extraction-field"><span class="extraction-field-label">Age</span><span class="extraction-field-value" [class.not-stated]="extraction!.icsr!.patient_age === 'Not stated'">{{ extraction!.icsr!.patient_age }}</span></div>
            <div class="extraction-field"><span class="extraction-field-label">Sex</span><span class="extraction-field-value" [class.not-stated]="extraction!.icsr!.patient_sex === 'Not stated'">{{ extraction!.icsr!.patient_sex }}</span></div>
            <div class="extraction-field"><span class="extraction-field-label">Weight</span><span class="extraction-field-value" [class.not-stated]="extraction!.icsr!.patient_weight === 'Not stated'">{{ extraction!.icsr!.patient_weight }}</span></div>
            <div class="extraction-field"><span class="extraction-field-label">History</span><span class="extraction-field-value" [class.not-stated]="extraction!.icsr!.patient_history === 'Not stated'">{{ extraction!.icsr!.patient_history }}</span></div>
          </div>

          <div class="extraction-group">
            <div class="extraction-group-title">Reporter</div>
            <div class="extraction-field"><span class="extraction-field-label">Name</span><span class="extraction-field-value">{{ extraction!.icsr!.reporter_name }}</span></div>
            <div class="extraction-field"><span class="extraction-field-label">Role</span><span class="extraction-field-value">{{ extraction!.icsr!.reporter_role }}</span></div>
            <div class="extraction-field"><span class="extraction-field-label">Country</span><span class="extraction-field-value">{{ extraction!.icsr!.reporter_country }}</span></div>
          </div>

          <div class="extraction-group">
            <div class="extraction-group-title">Product</div>
            <div class="extraction-field"><span class="extraction-field-label">Name</span><span class="extraction-field-value" style="color: var(--accent-secondary); font-weight: 600;">{{ extraction!.icsr!.product_name }}</span></div>
            <div class="extraction-field"><span class="extraction-field-label">Dose</span><span class="extraction-field-value">{{ extraction!.icsr!.product_dose }}</span></div>
            <div class="extraction-field"><span class="extraction-field-label">Route</span><span class="extraction-field-value">{{ extraction!.icsr!.product_route }}</span></div>
            <div class="extraction-field"><span class="extraction-field-label">Start Date</span><span class="extraction-field-value">{{ extraction!.icsr!.product_start_date }}</span></div>
            <div class="extraction-field"><span class="extraction-field-label">Stop Date</span><span class="extraction-field-value">{{ extraction!.icsr!.product_stop_date }}</span></div>
          </div>

          <div class="extraction-group">
            <div class="extraction-group-title">Reaction</div>
            <div class="extraction-field"><span class="extraction-field-label">Description</span><span class="extraction-field-value" style="color: var(--color-icsr);">{{ extraction!.icsr!.reaction_description }}</span></div>
            <div class="extraction-field"><span class="extraction-field-label">Onset Date</span><span class="extraction-field-value">{{ extraction!.icsr!.reaction_onset_date }}</span></div>
            <div class="extraction-field"><span class="extraction-field-label">Outcome</span><span class="extraction-field-value">{{ extraction!.icsr!.reaction_outcome }}</span></div>
          </div>

          <div class="extraction-group">
            <div class="extraction-group-title">Severity</div>
            <div class="extraction-field">
              <span class="extraction-field-label">Serious?</span>
              <span [class]="'badge ' + (extraction!.icsr!.is_serious === 'Yes' ? 'badge-icsr' : extraction!.icsr!.is_serious === 'No' ? 'badge-completed' : 'badge-pending')">{{ extraction!.icsr!.is_serious }}</span>
            </div>
            <div class="extraction-field"><span class="extraction-field-label">Criteria</span><span class="extraction-field-value">{{ extraction!.icsr!.seriousness_criteria }}</span></div>
          </div>

          <!-- Narrative -->
          <div style="margin-top: 12px; padding: 12px; background: rgba(6,182,212,0.05); border-radius: 8px; border-left: 3px solid var(--accent-secondary);">
            <div style="font-size: 11px; font-weight: 600; color: var(--accent-secondary); margin-bottom: 6px;">AI NARRATIVE</div>
            <p style="font-size: 13px; color: var(--text-secondary); line-height: 1.6;">{{ extraction!.icsr!.ai_narrative }}</p>
          </div>
        </div>

        <!-- PQC Extraction -->
        <div *ngIf="extraction?.pqc" class="card" style="margin-bottom: 16px;">
          <div class="card-header"><span class="card-title">🔧 Quality Complaint Extraction</span></div>
          <div class="extraction-field"><span class="extraction-field-label">Product</span><span class="extraction-field-value">{{ extraction!.pqc!.product_name }}</span></div>
          <div class="extraction-field"><span class="extraction-field-label">Batch/Lot #</span><span class="extraction-field-value" style="font-weight: 600;">{{ extraction!.pqc!.batch_lot_number }}</span></div>
          <div class="extraction-field"><span class="extraction-field-label">Description</span><span class="extraction-field-value">{{ extraction!.pqc!.complaint_description }}</span></div>
          <div class="extraction-field"><span class="extraction-field-label">Photo?</span><span class="extraction-field-value">{{ extraction!.pqc!.photo_mentioned }}</span></div>
        </div>

        <!-- MI Extraction -->
        <div *ngIf="extraction?.mi" class="card" style="margin-bottom: 16px;">
          <div class="card-header"><span class="card-title">ℹ Info Request Extraction</span></div>
          <div class="extraction-field"><span class="extraction-field-label">Topic</span><span class="extraction-field-value">{{ extraction!.mi!.product_topic }}</span></div>
          <div style="margin-top: 8px;">
            <div style="font-size: 11px; font-weight: 600; color: var(--text-muted); margin-bottom: 6px;">QUESTIONS ASKED</div>
            <ul style="padding-left: 16px;">
              <li *ngFor="let q of extraction!.mi!.questions_asked" style="font-size: 13px; color: var(--text-secondary); margin-bottom: 4px;">{{ q }}</li>
            </ul>
          </div>
        </div>

        <!-- Audit Trail -->
        <div class="card">
          <div class="card-header">
            <span class="card-title">📋 Audit Trail</span>
            <button class="btn btn-outline btn-sm" (click)="loadAudit()">Refresh</button>
          </div>
          <div *ngFor="let entry of auditEntries" style="padding: 8px 0; border-bottom: 1px solid rgba(75,85,99,0.15); font-size: 12px;">
            <div style="display: flex; justify-content: space-between;">
              <span style="font-weight: 600;">{{ entry.action_type }}</span>
              <span style="color: var(--text-muted);">{{ formatDate(entry.timestamp) }}</span>
            </div>
            <div style="color: var(--text-secondary); margin-top: 2px;">by {{ entry.performed_by }}</div>
          </div>
          <div *ngIf="auditEntries.length === 0" style="padding: 12px 0; color: var(--text-muted); font-size: 12px;">No audit entries yet.</div>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div *ngIf="!message" style="padding: 60px; text-align: center;">
      <div class="spinner" style="margin: 0 auto;"></div>
      <p style="margin-top: 12px; color: var(--text-muted);">Loading message...</p>
    </div>
  `
})
export class DocumentViewerComponent implements OnInit {
  messageId = 0;
  message: EmailMessageResponse | null = null;
  extraction: ExtractionSummary | null = null;
  classifications: Classification[] = [];
  auditEntries: AuditLogEntry[] = [];
  notification = '';
  reprocessing = false;
  overridingId = 0;
  overrideCategory = 'NOT_RELEVANT';
  overrideNotes = '';

  constructor(private route: ActivatedRoute, private api: ApiService) {}

  ngOnInit() {
    this.messageId = Number(this.route.snapshot.paramMap.get('id'));
    this.loadMessage();
    this.loadExtraction();
    this.loadAudit();
  }

  loadMessage() {
    this.api.getEmail(this.messageId).subscribe({
      next: (data) => {
        this.message = data;
        this.loadClassifications();
      },
      error: (err) => console.error(err)
    });
  }

  loadClassifications() {
    this.api.getReviewQueue().subscribe({
      next: (queue) => {
        const item = queue.find(q => q.message_id === this.messageId);
        if (item) this.classifications = item.classifications as Classification[];
      }
    });
  }

  loadExtraction() {
    this.api.getExtraction(this.messageId).subscribe({
      next: (data) => this.extraction = data,
      error: (err) => console.error(err)
    });
  }

  loadAudit() {
    this.api.getMessageAudit(this.messageId).subscribe({
      next: (data) => this.auditEntries = data,
      error: (err) => console.error(err)
    });
  }

  accept(clf: Classification) {
    this.api.acceptClassification(clf.classification_id).subscribe({
      next: () => {
        this.notification = `Classification "${clf.category}" accepted.`;
        clf.reviewer_action = 'ACCEPTED';
        this.loadAudit();
      }
    });
  }

  showOverride(clf: Classification) {
    this.overridingId = clf.classification_id;
    this.overrideCategory = clf.category;
    this.overrideNotes = '';
  }

  submitOverride(clf: Classification) {
    this.api.overrideClassification(clf.classification_id, this.overrideCategory, 'reviewer', this.overrideNotes).subscribe({
      next: () => {
        this.notification = `Classification overridden to "${this.overrideCategory}".`;
        clf.reviewer_action = 'OVERRIDDEN';
        clf.reviewer_override = this.overrideCategory;
        this.overridingId = 0;
        this.loadAudit();
      }
    });
  }

  reject(clf: Classification) {
    this.api.rejectClassification(clf.classification_id, 'reviewer').subscribe({
      next: () => {
        this.notification = `Classification "${clf.category}" rejected.`;
        clf.reviewer_action = 'REJECTED';
        this.loadAudit();
      }
    });
  }

  reprocess() {
    this.reprocessing = true;
    this.api.processEmail(this.messageId).subscribe({
      next: (data) => {
        this.notification = data.message;
        this.reprocessing = false;
        setTimeout(() => { this.loadMessage(); this.loadExtraction(); this.loadAudit(); }, 5000);
      },
      error: () => { this.reprocessing = false; }
    });
  }

  getCategoryLabel(key: string): string {
    const labels: { [k: string]: string } = { 'ICSR': '⚠ Safety Report', 'PQC': '🔧 Quality', 'MI': 'ℹ Info', 'NOT_RELEVANT': '— Not Relevant' };
    return labels[key] || key;
  }

  getConfClass(score: number): string {
    if (score >= 0.8) return 'high'; if (score >= 0.5) return 'medium'; return 'low';
  }

  formatDate(date: string | null | undefined): string {
    if (!date) return '';
    return new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  }
}
