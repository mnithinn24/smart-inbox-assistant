import { Component } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <div class="app-layout">
      <!-- Sidebar -->
      <aside class="sidebar">
        <div class="sidebar-logo">
          <h1>⚕ Smart Inbox</h1>
          <p>Healthcare Document AI</p>
        </div>
        <nav class="sidebar-nav">
          <a class="nav-item" routerLink="/dashboard" routerLinkActive="active">
            <span class="icon">📊</span> Dashboard
          </a>
          <a class="nav-item" routerLink="/inbox" routerLinkActive="active">
            <span class="icon">📬</span> Inbox Queue
          </a>
          <a class="nav-item" routerLink="/audit" routerLinkActive="active">
            <span class="icon">📋</span> Audit Log
          </a>
          <a class="nav-item" routerLink="/literature" routerLinkActive="active">
            <span class="icon">📄</span> Literature
            <span class="nav-badge">Bonus</span>
          </a>
        </nav>
        <div style="padding: 16px 20px; border-top: 1px solid var(--border-color); margin-top: auto;">
          <p style="font-size: 11px; color: var(--text-muted);">Clinevo Smart Inbox v1.0</p>
          <p style="font-size: 10px; color: var(--text-muted); margin-top: 2px;">Powered by Gemini Pro</p>
        </div>
      </aside>

      <!-- Main Content -->
      <main class="main-content">
        <router-outlet></router-outlet>
      </main>
    </div>
  `,
  styles: []
})
export class AppComponent {}
