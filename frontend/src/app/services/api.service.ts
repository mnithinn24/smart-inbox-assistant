import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  EmailListItem, EmailMessageResponse, ReviewQueueItem, ReviewStats,
  ExtractionSummary, AuditLogEntry, LiteratureArticle, LiteratureCase
} from '../models/interfaces';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private baseUrl = 'http://localhost:8000/api';

  constructor(private http: HttpClient) {}

  // ── Emails ──
  fetchEmails(maxEmails: number = 10): Observable<any> {
    return this.http.post(`${this.baseUrl}/emails/fetch`, { max_emails: maxEmails });
  }

  getEmails(status?: string, limit: number = 50): Observable<EmailListItem[]> {
    let params = new HttpParams().set('limit', limit.toString());
    if (status) params = params.set('status', status);
    return this.http.get<EmailListItem[]>(`${this.baseUrl}/emails`, { params });
  }

  getEmail(messageId: number): Observable<EmailMessageResponse> {
    return this.http.get<EmailMessageResponse>(`${this.baseUrl}/emails/${messageId}`);
  }

  processEmail(messageId: number): Observable<any> {
    return this.http.post(`${this.baseUrl}/emails/${messageId}/process`, {});
  }

  // ── Review ──
  getReviewQueue(status?: string, category?: string): Observable<ReviewQueueItem[]> {
    let params = new HttpParams();
    if (status) params = params.set('status', status);
    if (category) params = params.set('category', category);
    return this.http.get<ReviewQueueItem[]>(`${this.baseUrl}/review/queue`, { params });
  }

  getReviewStats(): Observable<ReviewStats> {
    return this.http.get<ReviewStats>(`${this.baseUrl}/review/stats`);
  }

  acceptClassification(classificationId: number, reviewedBy: string = 'reviewer', notes?: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/review/${classificationId}/accept`, {
      reviewed_by: reviewedBy, notes
    });
  }

  overrideClassification(classificationId: number, newCategory: string, reviewedBy: string = 'reviewer', notes?: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/review/${classificationId}/override`, {
      new_category: newCategory, reviewed_by: reviewedBy, notes
    });
  }

  rejectClassification(classificationId: number, reviewedBy: string = 'reviewer', reason?: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/review/${classificationId}/reject`, {
      reviewed_by: reviewedBy, reason
    });
  }

  // ── Documents ──
  getExtraction(messageId: number): Observable<ExtractionSummary> {
    return this.http.get<ExtractionSummary>(`${this.baseUrl}/documents/${messageId}/extraction`);
  }

  uploadDocument(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post(`${this.baseUrl}/documents/upload`, formData);
  }

  // ── Audit ──
  getAuditLog(messageId?: number, page: number = 1): Observable<any> {
    let params = new HttpParams().set('page', page.toString());
    if (messageId) params = params.set('message_id', messageId.toString());
    return this.http.get(`${this.baseUrl}/audit`, { params });
  }

  getMessageAudit(messageId: number): Observable<AuditLogEntry[]> {
    return this.http.get<AuditLogEntry[]>(`${this.baseUrl}/audit/${messageId}`);
  }

  // ── Literature ──
  uploadArticles(files: File[]): Observable<any> {
    const formData = new FormData();
    files.forEach(f => formData.append('files', f));
    return this.http.post(`${this.baseUrl}/literature/upload`, formData);
  }

  getArticles(): Observable<LiteratureArticle[]> {
    return this.http.get<LiteratureArticle[]>(`${this.baseUrl}/literature`);
  }

  getArticleCases(articleId: number): Observable<any> {
    return this.http.get(`${this.baseUrl}/literature/${articleId}/cases`);
  }
}
