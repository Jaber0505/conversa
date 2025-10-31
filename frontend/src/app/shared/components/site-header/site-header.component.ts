import {Component, inject, OnInit, ChangeDetectorRef} from '@angular/core';
import {ActivatedRoute, Router, RouterLink, UrlSegmentGroup, NavigationEnd} from '@angular/router';
import { filter } from 'rxjs/operators';
import { CommonModule } from '@angular/common';
import { LanguagePopoverComponent, type Lang } from '../language-popover/language-popover.component';
import { SHARED_IMPORTS } from '@shared';
import { TPipe } from '@core/i18n';
import {AuthApiService, AuthTokenService} from "@core/http";
import {Observable, of} from "rxjs";
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
export class SiteHeaderComponent implements OnInit {
  langs: ReadonlyArray<Lang> = ['fr', 'en', 'nl'] as const;
  private _showLang = false;
  protected authApi = inject(AuthApiService);
  protected tokens = inject(AuthTokenService);
  constructor(private router: Router, private route: ActivatedRoute, private cdr: ChangeDetectorRef) {}

  showLang() { return this._showLang; }
  openLang() { this._showLang = true; }
  closeLang() { this._showLang = false; }
  me$: Observable<MeRes | null> = of(null);

  ngOnInit(): void {
    this.updateMeStream();
    // Re-évaluer après chaque navigation (ex: login → redirect events)
    this.router.events.pipe(filter(e => e instanceof NavigationEnd)).subscribe(() => {
      this.updateMeStream();
    });
  }

  private updateMeStream() {
    this.me$ = this.tokens.hasAccess() ? this.authApi.me() : of(null);
    // Force la détection au cas où
    this.cdr.markForCheck?.();
  }
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
