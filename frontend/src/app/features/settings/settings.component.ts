// src/app/features/settings/settings.component.ts
import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

// ⬇️ i18n via barrel
import { TPipe, TAttrDirective, TDatePipe, TNumberPipe, TCurrencyPipe, THtmlDirective, LangService } from '@core/i18n';
import type { Lang } from '@core/i18n';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, RouterLink, TPipe, TAttrDirective, TDatePipe, TNumberPipe, TCurrencyPipe, THtmlDirective],
  templateUrl: './settings.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SettingsComponent {
  private readonly lang = inject(LangService);

  readonly today = new Date();
  readonly users = 12345.6789;
  readonly price = 1234.5;

  get currentLang(): Lang { return this.lang.current; }
  set(code: Lang) { this.lang.set(code); }
}
