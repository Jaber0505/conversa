// src/app/features/about/about.component.ts
import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { TPipe } from '@app/core/i18n/t.pipe';
import { TDatePipe, TNumberPipe, TCurrencyPipe } from '@app/core/i18n/i18n.pipes';
import { LangService } from '@app/core/i18n/lang.service';
import type { Lang } from '@app/core/i18n/languages.config';

// ⬇️ seulement si tu veux formater en TS (facultatif)
import { formatDateIntl, formatNumberIntl, formatCurrencyIntl } from '@app/core/i18n/intl.helpers';

@Component({
  selector: 'app-about',
  standalone: true,
  imports: [CommonModule, RouterLink, TPipe, TDatePipe, TNumberPipe, TCurrencyPipe],
  templateUrl: './about.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AboutComponent {
  private readonly lang = inject(LangService);

  // utilisé dans le template avec les pipes
  readonly today = new Date();

  // ⬇️ exemples d’usage “depuis le TS” (optionnels)
  get todayShortLabel(): string {
    return formatDateIntl(this.today, this.lang.current, { dateStyle: 'short' });
  }
  get totalUsersLabel(): string {
    return formatNumberIntl(12345.6789, this.lang.current, { maximumFractionDigits: 0 });
  }
  get priceLabel(): string {
    return formatCurrencyIntl(1234.5, this.lang.current, 'EUR');
  }

  get currentLang(): Lang { return this.lang.current; }
  set(code: Lang) { this.lang.set(code); }
}
