import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { ReviewStats } from '../../models/interfaces';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <div class="page-header">
      <h2>Dashboard</h2>
      <p>Smart Inbox Assistant — AI-powered healthcare document processing</p>
    </div>

    <!-- Action Buttons -->
    <div style="display: flex; gap: 12px; margin-bottom: 24px;">
      <button class="btn btn-primary" (click)="fetchEmails()" [disabled]="fetching">
        {{ fetching ? '⟳ Fetching...' : '📬 Fetch New Emails' }}
      </button>
      <button class="btn btn-outline" routerLink="/inbox">
        📋 View Inbox Queue
      </button>
    </div>

    <!-- Notification -->
    <div *ngIf="notification" class="card animate-in" style="margin-bottom: 16px; border-color: rgba(16, 185, 129, 0.3); background: rgba(16, 185, 129, 0.05);">
      <span style="color: var(--color-success);">✓</span> {{ notification }}
    </div>

    <!-- Stats Grid -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">Total Messages</div>
        <div class="stat-value">{{ stats?.total_messages || 0 }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Pending Review</div>
        <div class="stat-value" style="background: linear-gradient(135deg, #8b5cf6, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">{{ stats?.pending_review || 0 }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Accepted</div>
        <div class="stat-value" style="background: linear-gradient(135deg, #10b981, #34d399); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">{{ stats?.accepted || 0 }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Overridden</div>
        <div class="stat-value" style="background: linear-gradient(135deg, #f59e0b, #fbbf24); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">{{ stats?.overridden || 0 }}</div>
      </div>
    </div>

    <!-- Category Breakdown & Metrics -->
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
      <div class="card">
        <div class="card-header">
          <span class="card-title">By Category</span>
        </div>
        <div *ngIf="stats?.by_category">
          <div *ngFor="let cat of categoryList" style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid rgba(75,85,99,0.15);">
            <span [class]="'badge badge-' + cat.key.toLowerCase().replace('_','-')">{{ getCategoryLabel(cat.key) }}</span>
            <span style="font-size: 20px; font-weight: 700; color: var(--text-primary);">{{ cat.value }}</span>
          </div>
          <div *ngIf="categoryList.length === 0" class="empty-state" style="padding: 20px;">
            <p>No classifications yet</p>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <span class="card-title">Performance</span>
        </div>
        <div style="padding: 10px 0; border-bottom: 1px solid rgba(75,85,99,0.15); display: flex; justify-content: space-between;">
          <span style="color: var(--text-secondary); font-size: 13px;">Avg Processing Time</span>
          <span style="font-weight: 600;">{{ getAvgTime() }}</span>
        </div>
        <div style="padding: 10px 0; border-bottom: 1px solid rgba(75,85,99,0.15); display: flex; justify-content: space-between;">
          <span style="color: var(--text-secondary); font-size: 13px;">Avg Confidence</span>
          <span style="font-weight: 600;">{{ getAvgConfidence() }}</span>
        </div>
        <div style="padding: 10px 0; display: flex; justify-content: space-between;">
          <span style="color: var(--text-secondary); font-size: 13px;">AI Model</span>
          <span style="font-weight: 600; color: var(--accent-secondary);">Gemini Pro</span>
        </div>
      </div>
    </div>
  `
})
export class DashboardComponent implements OnInit {
  stats: ReviewStats | null = null;
  categoryList: { key: string; value: number }[] = [];
  fetching = false;
  notification = '';

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.loadStats();
  }

  loadStats() {
    this.api.getReviewStats().subscribe({
      next: (data) => {
        this.stats = data;
        this.categoryList = Object.entries(data.by_category || {}).map(([key, value]) => ({ key, value }));
      },
      error: (err) => console.error('Stats error:', err)
    });
  }

  fetchEmails() {
    this.fetching = true;
    this.notification = '';
    this.api.fetchEmails(10).subscribe({
      next: (data) => {
        this.fetching = false;
        this.notification = data.message;
        setTimeout(() => this.loadStats(), 2000);
      },
      error: (err) => {
        this.fetching = false;
        this.notification = 'Failed to fetch emails: ' + (err.error?.detail || err.message);
      }
    });
  }

  getCategoryLabel(key: string): string {
    const labels: { [k: string]: string } = {
      'ICSR': '⚠ Safety Report',
      'PQC': '🔧 Quality Complaint',
      'MI': 'ℹ Info Request',
      'NOT_RELEVANT': '— Not Relevant'
    };
    return labels[key] || key;
  }

  getAvgTime(): string {
    if (this.stats && this.stats.avg_processing_time_ms) {
      return (this.stats.avg_processing_time_ms / 1000).toFixed(1) + 's';
    }
    return 'N/A';
  }

  getAvgConfidence(): string {
    if (this.stats && this.stats.avg_confidence) {
      return (this.stats.avg_confidence * 100).toFixed(0) + '%';
    }
    return 'N/A';
  }
}
