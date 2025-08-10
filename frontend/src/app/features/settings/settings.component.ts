// src/app/features/settings/settings.component.ts
import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

import { TPipe } from '@app/core/i18n/t.pipe';
import { TAttrDirective } from '@app/core/i18n/t-attr.directive';
import { TDatePipe, TNumberPipe, TCurrencyPipe } from '@app/core/i18n/i18n.pipes';
import { THtmlDirective } from '@app/core/i18n/t-html.directive';

import { LangService } from '@app/core/i18n/lang.service';
import type { Lang } from '@app/core/i18n/languages.config';

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
