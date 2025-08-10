import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { I18nService } from '@app/core/i18n/i18n.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet],
  template: `
    <ng-container *ngIf="ready$ | async; else splash">
      <router-outlet />
    </ng-container>

    <ng-template #splash>
      <!-- Splash minimal pour éviter le flash de clés -->
      <div style="min-height: 100vh;"></div>
    </ng-template>
  `,
})
export class App {
  readonly ready$ = inject(I18nService).ready$;
}
