import {Component, inject} from '@angular/core';
import { Router, RouterLink, UrlSegmentGroup } from '@angular/router';
import { CommonModule } from '@angular/common';
import { LanguagePopoverComponent, type Lang } from '../language-popover/language-popover.component';
import { SHARED_IMPORTS } from '@shared';
import { TPipe } from '@core/i18n';
import {AuthApiService, AuthTokenService} from "@core/http";

@Component({
  standalone: true,
  selector: 'app-site-header',
  templateUrl: './site-header.component.html',
  styleUrls: ['./site-header.component.scss'],
  imports: [
    CommonModule,
    RouterLink,
    LanguagePopoverComponent,
    TPipe,
    ...SHARED_IMPORTS,
  ],
})
export class SiteHeaderComponent {
  langs: ReadonlyArray<Lang> = ['fr', 'en', 'nl'] as const;
  private _showLang = false;
  private authApi = inject(AuthApiService);
  private tokens = inject(AuthTokenService);
  constructor(private router: Router) {}

  showLang() { return this._showLang; }
  openLang() { this._showLang = true; }
  closeLang() { this._showLang = false; }

  langCode(): Lang {
    const tree = this.router.parseUrl(this.router.url);
    const primary: UrlSegmentGroup | undefined = tree.root.children['primary'];
    const segs = primary?.segments ?? [];
    const code = segs[0]?.path as Lang | undefined;
    return (code && (['fr', 'en', 'nl'] as const).includes(code)) ? code : 'fr';
  }
  currentLang(): Lang { return this.langCode(); }

  // clé i18n pour le libellé de langue complet
  langLabelKey(): string { return `languages.${this.langCode()}`; }
  loading = false;
  confirmLang(next: Lang) {
    const tree = this.router.parseUrl(this.router.url);
    const primary: UrlSegmentGroup | undefined = tree.root.children['primary'];
    const segs = primary?.segments.map(s => s.path) ?? [];
    const newSegs = segs.length ? [next, ...segs.slice(1)] : [next];

    this.router.navigate(['/', ...newSegs], {
      queryParams: tree.queryParams,
      fragment: tree.fragment ?? undefined,
      replaceUrl: true,
    });

    this._showLang = false;
  }

  onLogout() {
    if (this.loading) return;
    this.loading = true;

    const refresh = this.tokens.refresh;
    debugger;
    this.authApi.logout(refresh!).subscribe({
      next: () => { this.loading = false;
        this.tokens.clear();
        debugger; },

      error: () => { this.loading = false; }, // on nettoie quand même
    });
  }
}
