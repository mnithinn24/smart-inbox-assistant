import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';
import { LiteratureArticle } from '../../models/interfaces';

@Component({
  selector: 'app-literature',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="page-header">
      <h2>Literature Screening <span class="badge badge-mi" style="margin-left: 8px; font-size: 11px;">Bonus</span></h2>
      <p>Upload published article PDFs to screen for reportable patient safety cases</p>
    </div>

    <!-- Upload Area -->
    <div class="card" style="margin-bottom: 24px; text-align: center; padding: 40px; border-style: dashed; cursor: pointer;"
         (click)="fileInput.click()"
         (dragover)="$event.preventDefault()" (drop)="onDrop($event)">
      <input #fileInput type="file" accept=".pdf" multiple (change)="onFileSelect($event)" style="display: none;">
      <div style="font-size: 36px; margin-bottom: 12px;">📄</div>
      <h3 style="font-size: 16px; margin-bottom: 8px;">Drop article PDFs here or click to upload</h3>
      <p style="color: var(--text-muted); font-size: 13px;">Supports multiple PDF files. Each will be screened for reportable patient cases.</p>
    </div>

    <!-- Notification -->
    <div *ngIf="notification" class="card animate-in" style="margin-bottom: 16px; padding: 12px 20px; border-color: rgba(59,130,246,0.3);">
      {{ notification }}
    </div>

    <!-- Articles List -->
    <div *ngIf="articles.length > 0" class="card" style="padding: 0; overflow: hidden;">
      <table class="data-table">
        <thead>
          <tr>
            <th>File</th>
            <th>Status</th>
            <th>Cases Found</th>
            <th>Time</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let art of articles" class="animate-in">
            <td style="font-weight: 500;">📄 {{ art.filename }}</td>
            <td><span [class]="'badge badge-' + art.processing_status.toLowerCase()">{{ art.processing_status }}</span></td>
            <td>
              <span *ngIf="art.cases_found > 0" style="color: var(--color-icsr); font-weight: 700; font-size: 18px;">{{ art.cases_found }}</span>
              <span *ngIf="art.cases_found === 0" style="color: var(--text-muted);">0</span>
            </td>
            <td style="font-size: 12px; color: var(--text-muted);">{{ art.processing_time_ms ? (art.processing_time_ms / 1000).toFixed(1) + 's' : '—' }}</td>
            <td>
              <button *ngIf="art.processing_status === 'COMPLETED'" class="btn btn-outline btn-sm" (click)="viewCases(art)">View Cases</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Cases Detail -->
    <div *ngIf="selectedCases.length > 0" class="card animate-in" style="margin-top: 16px;">
      <div class="card-header">
        <span class="card-title">📋 Cases in: {{ selectedArticleName }}</span>
        <button class="btn btn-outline btn-sm" (click)="selectedCases = []">Close</button>
      </div>
      <div *ngFor="let c of selectedCases" style="padding: 16px; margin-bottom: 8px; background: rgba(17,24,39,0.5); border-radius: 8px; border: 1px solid var(--border-color);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
          <span style="font-weight: 600;">Case #{{ c.case_number }}</span>
          <div style="display: flex; gap: 8px;">
            <span [class]="'badge ' + (c.is_reportable === 'Yes' ? 'badge-icsr' : 'badge-not-relevant')">
              {{ c.is_reportable === 'Yes' ? '⚠ Reportable' : 'Not Reportable' }}
            </span>
            <div class="confidence-bar">
              <span class="confidence-label">{{ (c.confidence_score * 100).toFixed(0) }}%</span>
            </div>
          </div>
        </div>
        <p style="font-size: 13px; color: var(--text-secondary); margin-bottom: 6px;">{{ c.case_summary }}</p>
        <p style="font-size: 12px; color: var(--text-muted);">
          <strong>Relevance:</strong> {{ c.relevance_reason }}
        </p>
        <p *ngIf="c.source_location" style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">📍 {{ c.source_location }}</p>
      </div>
    </div>
  `
})
export class LiteratureComponent implements OnInit {
  articles: LiteratureArticle[] = [];
  selectedCases: any[] = [];
  selectedArticleName = '';
  notification = '';

  constructor(private api: ApiService) {}

  ngOnInit() { this.loadArticles(); }

  loadArticles() {
    this.api.getArticles().subscribe({
      next: (data) => this.articles = data,
      error: (err) => console.error(err)
    });
  }

  onFileSelect(event: any) {
    const files = Array.from(event.target.files) as File[];
    if (files.length === 0) return;
    this.uploadFiles(files);
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    const files = Array.from(event.dataTransfer?.files || []).filter(f => f.name.endsWith('.pdf'));
    if (files.length > 0) this.uploadFiles(files);
  }

  uploadFiles(files: File[]) {
    this.notification = `Uploading ${files.length} file(s)...`;
    this.api.uploadArticles(files).subscribe({
      next: (data) => {
        this.notification = `Uploaded ${data.uploaded} articles. Processing...`;
        setTimeout(() => this.loadArticles(), 3000);
      },
      error: (err) => { this.notification = 'Upload failed: ' + (err.error?.detail || err.message); }
    });
  }

  viewCases(article: LiteratureArticle) {
    this.selectedArticleName = article.filename;
    this.api.getArticleCases(article.article_id).subscribe({
      next: (data) => this.selectedCases = data.cases || [],
      error: (err) => console.error(err)
    });
  }
}
