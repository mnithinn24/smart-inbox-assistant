import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { ReviewQueueItem } from '../../models/interfaces';

@Component({
  selector: 'app-inbox-queue',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  template: `
    <div class="page-header">
      <h2>Inbox Queue</h2>
      <p>Review AI-classified incoming messages and documents</p>
    </div>

    <!-- Filters & Actions -->
    <div style="display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; align-items: center;">
      <button class="btn btn-primary" (click)="fetchEmails()" [disabled]="fetching">
        {{ fetching ? '⟳ Fetching...' : '📬 Fetch Emails' }}
      </button>

      <label class="btn btn-outline" style="cursor: pointer;">
        📎 Upload PDF
        <input type="file" accept=".pdf" (change)="uploadFile($event)" style="display: none;">
      </label>

      <div style="margin-left: auto; display: flex; gap: 8px;">
        <select class="form-select" style="width: auto; padding: 6px 12px;" [(ngModel)]="filterStatus" (change)="loadQueue()">
          <option value="">All Statuses</option>
          <option value="PENDING">Pending</option>
          <option value="ACCEPTED">Accepted</option>
          <option value="OVERRIDDEN">Overridden</option>
        </select>
        <select class="form-select" style="width: auto; padding: 6px 12px;" [(ngModel)]="filterCategory" (change)="loadQueue()">
          <option value="">All Categories</option>
          <option value="ICSR">Safety Report</option>
          <option value="PQC">Quality Complaint</option>
          <option value="MI">Info Request</option>
          <option value="NOT_RELEVANT">Not Relevant</option>
        </select>
      </div>
    </div>

    <!-- Notification -->
    <div *ngIf="notification" class="card animate-in" style="margin-bottom: 16px; padding: 12px 20px; border-color: rgba(59, 130, 246, 0.3);">
      {{ notification }}
    </div>

    <!-- Queue Table -->
    <div class="card" style="padding: 0; overflow: hidden;">
      <table class="data-table" *ngIf="queue.length > 0">
        <thead>
          <tr>
            <th>ID</th>
            <th>Date</th>
            <th>Sender</th>
            <th>Subject</th>
            <th>Category</th>
            <th>Confidence</th>
            <th>Status</th>
            <th>📎</th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let item of queue" [routerLink]="['/inbox', item.message_id]" class="animate-in">
            <td style="color: var(--text-muted); font-size: 12px;">#{{ item.message_id }}</td>
            <td style="font-size: 12px; white-space: nowrap;">{{ formatDate(item.received_date) }}</td>
            <td style="max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{ item.sender || 'Unknown' }}</td>
            <td style="max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 500;">{{ item.subject || 'No subject' }}</td>
            <td>
              <div style="display: flex; gap: 4px; flex-wrap: wrap;">
                <span *ngFor="let clf of item.classifications" [class]="'badge badge-' + clf.category.toLowerCase().replace('_','-')">
                  {{ clf.category }}
                </span>
              </div>
            </td>
            <td>
              <div *ngIf="getMaxConfidence(item) !== null" class="confidence-bar">
                <div class="confidence-track">
                  <div class="confidence-fill" [class]="getConfidenceClass(getMaxConfidence(item)!)" [style.width.%]="getMaxConfidence(item)! * 100"></div>
                </div>
                <span class="confidence-label" [style.color]="getConfidenceColor(getMaxConfidence(item)!)">{{ (getMaxConfidence(item)! * 100).toFixed(0) }}%</span>
              </div>
            </td>
            <td>
              <span [class]="'badge badge-' + getReviewStatus(item).toLowerCase()">{{ getReviewStatus(item) }}</span>
            </td>
            <td style="text-align: center; color: var(--text-muted);">{{ item.attachment_count }}</td>
          </tr>
        </tbody>
      </table>

      <div *ngIf="queue.length === 0 && !loading" class="empty-state">
        <div class="icon">📭</div>
        <h3>No messages yet</h3>
        <p>Click "Fetch Emails" to check your inbox, or upload a PDF directly.</p>
      </div>

      <div *ngIf="loading" style="padding: 40px; text-align: center;">
        <div class="spinner" style="margin: 0 auto;"></div>
        <p style="margin-top: 12px; color: var(--text-muted);">Loading...</p>
      </div>
    </div>
  `
})
export class InboxQueueComponent implements OnInit {
  queue: ReviewQueueItem[] = [];
  loading = false;
  fetching = false;
  notification = '';
  filterStatus = '';
  filterCategory = '';

  constructor(private api: ApiService) {}

  ngOnInit() { this.loadQueue(); }

  loadQueue() {
    this.loading = true;
    this.api.getReviewQueue(this.filterStatus || undefined, this.filterCategory || undefined).subscribe({
      next: (data) => { this.queue = data; this.loading = false; },
      error: (err) => { console.error(err); this.loading = false; }
    });
  }

  fetchEmails() {
    this.fetching = true;
    this.notification = '';
    this.api.fetchEmails(10).subscribe({
      next: (data) => {
        this.fetching = false;
        this.notification = data.message;
        setTimeout(() => this.loadQueue(), 3000);
      },
      error: (err) => {
        this.fetching = false;
        this.notification = 'Error: ' + (err.error?.detail || err.message);
      }
    });
  }

  uploadFile(event: any) {
    const file = event.target.files[0];
    if (!file) return;
    this.notification = `Uploading ${file.name}...`;
    this.api.uploadDocument(file).subscribe({
      next: (data) => {
        this.notification = data.message;
        setTimeout(() => this.loadQueue(), 5000);
      },
      error: (err) => { this.notification = 'Upload failed: ' + (err.error?.detail || err.message); }
    });
  }

  getMaxConfidence(item: ReviewQueueItem): number | null {
    if (!item.classifications || item.classifications.length === 0) return null;
    return Math.max(...item.classifications.map(c => c.confidence_score));
  }

  getConfidenceClass(score: number): string {
    if (score >= 0.8) return 'high';
    if (score >= 0.5) return 'medium';
    return 'low';
  }

  getConfidenceColor(score: number): string {
    if (score >= 0.8) return 'var(--conf-high)';
    if (score >= 0.5) return 'var(--conf-medium)';
    return 'var(--conf-low)';
  }

  getReviewStatus(item: ReviewQueueItem): string {
    if (!item.classifications || item.classifications.length === 0) return 'pending';
    const actions = item.classifications.map(c => c.reviewer_action);
    if (actions.includes('OVERRIDDEN')) return 'overridden';
    if (actions.every(a => a === 'ACCEPTED')) return 'completed';
    return 'pending';
  }

  formatDate(date: string | null): string {
    if (!date) return '';
    return new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  }
}
