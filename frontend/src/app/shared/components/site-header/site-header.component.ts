import {Component, inject, OnInit} from '@angular/core';
import {ActivatedRoute, Router, RouterLink, UrlSegmentGroup} from '@angular/router';
import { CommonModule } from '@angular/common';
import { LanguagePopoverComponent, type Lang } from '../language-popover/language-popover.component';
import { SHARED_IMPORTS } from '@shared';
import { TPipe } from '@core/i18n';
import {AuthApiService, AuthTokenService} from "@core/http";
import {Observable} from "rxjs";
export type MeRes = {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  username?: string;
  age?: number;
  bio?: string;
  native_langs?: string[];
  target_langs?: string[];
  avatar?: string;
};
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
export class SiteHeaderComponent{
  langs: ReadonlyArray<Lang> = ['fr', 'en', 'nl'] as const;
  private _showLang = false;
  protected authApi = inject(AuthApiService);
  protected tokens = inject(AuthTokenService);
  constructor(private router: Router, private route: ActivatedRoute,) {}

  showLang() { return this._showLang; }
  openLang() { this._showLang = true; }
  closeLang() { this._showLang = false; }
  me$: Observable<MeRes> = this.authApi.me()
  langCode(): Lang {
    const tree = this.router.parseUrl(this.router.url);
    const primary: UrlSegmentGroup | undefined = tree.root.children['primary'];
    const segs = primary?.segments ?? [];
    const code = segs[0]?.path as Lang | undefined;
    return (code && (['fr', 'en', 'nl'] as const).includes(code)) ? code : 'fr';
  }
  currentLang(): Lang { return this.langCode(); }
  private lang(): string { return this.route.snapshot.paramMap.get('lang') ?? 'fr'; }
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
    this.authApi.logout(refresh!).subscribe({
      next: () => { this.loading = false;
        this.tokens.clear();
        this.router.navigate(['/', this.lang()]);
        },
      error: () => { this.loading = false; },
    });
  }
}
