// src/app/app.ts
import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterOutlet, NavigationEnd } from '@angular/router';
import { filter } from 'rxjs/operators';

import { I18nService, TPipe } from '@core/i18n';
import { SiteHeaderComponent } from '@app/shared/components/site-header/site-header.component';
import { SiteFooterComponent } from '@app/shared/components/site-footer/site-footer.component';
import { AuthTokenService } from '@core/http';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, TPipe, SiteHeaderComponent, SiteFooterComponent],
  template: `
    <ng-container *ngIf="ready$ | async; else splash">
      <div class="app-wrapper">
        <!-- Header toujours visible -->
        <app-site-header></app-site-header>

        <!-- Contenu principal -->
        <main class="app-content">
          <router-outlet></router-outlet>
        </main>

        <!-- Footer toujours visible et en bas -->
        <app-site-footer></app-site-footer>
      </div>
    </ng-container>

    <ng-template #splash>
      <div class="splash" role="status" aria-live="polite" aria-busy="true">
        <div class="spinner" aria-hidden="true"></div>
        <p class="splash__text">{{ 'common.loading' | t }}</p>
      </div>
    </ng-template>
  `,
  styleUrls: ['./app.component.scss']
})
export class App {
  private router = inject(Router);
  private authTokenService = inject(AuthTokenService);
  readonly ready$ = inject(I18nService).ready$;

  // Signal to track authentication status
  isAuthenticated = signal<boolean>(this.authTokenService.hasAccess());

  constructor() {
    // Update authentication status on route changes
    this.router.events
      .pipe(filter(event => event instanceof NavigationEnd))
      .subscribe(() => {
        this.isAuthenticated.set(this.authTokenService.hasAccess());
      });
  }
}
