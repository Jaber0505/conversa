// src/app/app.ts
import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';

import { I18nService, TPipe } from '@core/i18n';
import { SiteHeaderComponent } from '@app/shared/components/site-header/site-header.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, TPipe, SiteHeaderComponent],
  template: `
    <ng-container *ngIf="ready$ | async; else splash">
      <app-site-header></app-site-header>
      <router-outlet></router-outlet>
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
  readonly ready$ = inject(I18nService).ready$;
}
