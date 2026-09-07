import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { AuditLogEntry } from '../../models/interfaces';

@Component({
  selector: 'app-audit-log',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="page-header">
      <h2>Audit Log</h2>
      <p>Complete trail of all AI decisions and reviewer actions</p>
    </div>

    <div style="display: flex; gap: 12px; margin-bottom: 20px; align-items: center;">
      <input class="form-input" type="number" placeholder="Filter by Message ID" [(ngModel)]="filterMessageId"
             style="width: 200px; padding: 6px 12px;" (keyup.enter)="loadLog()">
      <select class="form-select" style="width: auto; padding: 6px 12px;" [(ngModel)]="filterAction" (change)="loadLog()">
        <option value="">All Actions</option>
        <option value="AI_CLASSIFY">AI Classify</option>
        <option value="AI_EXTRACT_ICSR">AI Extract ICSR</option>
        <option value="AI_EXTRACT_PQC">AI Extract PQC</option>
        <option value="AI_EXTRACT_MI">AI Extract MI</option>
        <option value="PDF_PROCESSED">PDF Processed</option>
        <option value="REVIEWER_ACCEPT">Reviewer Accept</option>
        <option value="REVIEWER_OVERRIDE">Reviewer Override</option>
        <option value="PIPELINE_ERROR">Pipeline Error</option>
      </select>
      <button class="btn btn-outline btn-sm" (click)="loadLog()">🔄 Refresh</button>
      <span style="margin-left: auto; color: var(--text-muted); font-size: 12px;">
        {{ entries.length }} entries · Page {{ page }}
      </span>
    </div>

    <div class="card" style="padding: 0; overflow: hidden;">
      <table class="data-table" *ngIf="entries.length > 0">
        <thead>
          <tr>
            <th>Time</th>
            <th>Msg ID</th>
            <th>Action</th>
            <th>Performed By</th>
            <th>Details</th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let entry of entries" class="animate-in">
            <td style="font-size: 12px; white-space: nowrap; color: var(--text-muted);">{{ formatDate(entry.timestamp) }}</td>
            <td><span *ngIf="entry.message_id" style="color: var(--accent-primary); cursor: pointer;">#{{ entry.message_id }}</span></td>
            <td><span [class]="'badge ' + getActionBadge(entry.action_type)">{{ entry.action_type }}</span></td>
            <td style="font-size: 12px;">{{ entry.performed_by }}</td>
            <td style="font-size: 11px; color: var(--text-secondary); max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
              {{ formatDetail(entry.action_detail) }}
            </td>
          </tr>
        </tbody>
      </table>

      <div *ngIf="entries.length === 0 && !loading" class="empty-state">
        <div class="icon">📋</div>
        <h3>No audit entries</h3>
        <p>Process some emails to generate audit trail entries.</p>
      </div>
    </div>

    <div *ngIf="entries.length > 0" style="display: flex; gap: 8px; margin-top: 16px; justify-content: center;">
      <button class="btn btn-outline btn-sm" [disabled]="page <= 1" (click)="page = page - 1; loadLog()">← Previous</button>
      <button class="btn btn-outline btn-sm" (click)="page = page + 1; loadLog()">Next →</button>
    </div>
  `
})
export class AuditLogComponent implements OnInit {
  entries: AuditLogEntry[] = [];
  loading = false;
  page = 1;
  filterMessageId: number | null = null;
  filterAction = '';

  constructor(private api: ApiService) {}

  ngOnInit() { this.loadLog(); }

  loadLog() {
    this.loading = true;
    this.api.getAuditLog(this.filterMessageId || undefined, this.page).subscribe({
      next: (data) => { this.entries = data.entries; this.loading = false; },
      error: (err) => { console.error(err); this.loading = false; }
    });
  }

  getActionBadge(action: string): string {
    if (action.startsWith('AI_')) return 'badge-mi';
    if (action.startsWith('REVIEWER_ACCEPT')) return 'badge-completed';
    if (action.startsWith('REVIEWER_OVERRIDE')) return 'badge-pqc';
    if (action.includes('ERROR')) return 'badge-error';
    return 'badge-pending';
  }

  formatDetail(detail: any): string {
    if (!detail) return '';
    if (typeof detail === 'string') return detail;
    return JSON.stringify(detail).substring(0, 100);
  }

  formatDate(date: string | null): string {
    if (!date) return '';
    return new Date(date).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }
}
