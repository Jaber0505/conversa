// src/app/features/home/home.component.ts
import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';

import { TPipe } from '@app/core/i18n/t.pipe';
import { RouterLink } from '@angular/router';
import { TAttrDirective } from '@app/core/i18n/t-attr.directive';
import { LangService } from '@app/core/i18n/lang.service';
import { TDatePipe, TNumberPipe, TCurrencyPipe } from '@app/core/i18n/i18n.pipes';
import type { Lang } from '@app/core/i18n/languages.config';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, RouterLink, TPipe, TAttrDirective],
  templateUrl: './home.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class HomeComponent {
  private readonly lang = inject(LangService);

  get currentLang(): Lang { return this.lang.current; }
    set(code: Lang) { this.lang.set(code); }
}
