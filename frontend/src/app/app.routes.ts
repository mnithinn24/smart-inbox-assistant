import { Routes } from '@angular/router';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { InboxQueueComponent } from './components/inbox-queue/inbox-queue.component';
import { DocumentViewerComponent } from './components/document-viewer/document-viewer.component';
import { AuditLogComponent } from './components/audit-log/audit-log.component';
import { LiteratureComponent } from './components/literature/literature.component';

export const routes: Routes = [
  { path: '', redirectTo: '/dashboard', pathMatch: 'full' },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'inbox', component: InboxQueueComponent },
  { path: 'inbox/:id', component: DocumentViewerComponent },
  { path: 'audit', component: AuditLogComponent },
  { path: 'literature', component: LiteratureComponent },
];
