import { DOCUMENT } from '@angular/common';
import { Inject, Injectable, inject } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { Router } from '@angular/router';
import { DEFAULT_LANGUAGE, STORAGE_KEY, SUPPORTED_LANGS, type Lang } from '@core/i18n';

@Injectable({ providedIn: 'root' })
export class LangService {
  private readonly _lang$ = new BehaviorSubject<Lang>(DEFAULT_LANGUAGE);
  readonly lang$ = this._lang$.asObservable();
  private readonly router = inject(Router);

  constructor(@Inject(DOCUMENT) private readonly doc: Document) {
    const detected = this.resolveInitialLang();
    this.apply(detected, { persist: false });
  }

  get current(): Lang { return this._lang$.value; }

  /** API unique : change la langue (+ URL par défaut) */
  set(lang: Lang, opts: { persist?: boolean; navigate?: boolean; reload?: boolean } = {}) {
    const persist = opts.persist ?? true;
    const navigate = opts.navigate ?? true;
    const reload = opts.reload ?? false;

    this.apply(lang, { persist });

    if (navigate) {
      this.updateUrlPrefix()
        .finally(() => this.reloadIfNeeded(reload));
    } else {
      this.reloadIfNeeded(reload);
    }
  }

  // --- interne ---
  private updateUrlPrefix(): Promise<boolean> {
    const url = this.router.url;
    const [pathAndQuery, fragment] = url.split('#');
    const [path, query] = pathAndQuery.split('?');

    const langRe = new RegExp(`^/(?:${SUPPORTED_LANGS.join('|')})(?=$|/)`);
    const rest = path.replace(langRe, ''); 
    const newPath = `/${this.current}${rest || ''}`;

    let newUrl = newPath;
    if (query) newUrl += `?${query}`;
    if (fragment) newUrl += `#${fragment}`;

    return this.router.navigateByUrl(newUrl, { replaceUrl: true });
  }

  private apply(code: Lang, opts: { persist: boolean }) {
    const safe = SUPPORTED_LANGS.includes(code) ? code : DEFAULT_LANGUAGE;
    this._lang$.next(safe);
    this.doc.documentElement.setAttribute('lang', safe);
    if (opts.persist) { try { localStorage.setItem(STORAGE_KEY, safe); } catch {} }
  }

  private reloadIfNeeded(reload: boolean): void {
    if (!reload || typeof window === 'undefined') return;
    // Laisser Angular mettre à jour l'URL avant de recharger
    setTimeout(() => window.location.reload(), 50);
  }

  private resolveInitialLang(): Lang {
    try {
      const fromStorage = localStorage.getItem(STORAGE_KEY) as Lang | null;
      if (fromStorage && SUPPORTED_LANGS.includes(fromStorage)) return fromStorage;
    } catch {}
    const prefs = (navigator.languages ?? [navigator.language])
      .filter(Boolean).map(l => l.toLowerCase().slice(0,2)) as Lang[];
    for (const p of prefs) if (SUPPORTED_LANGS.includes(p)) return p;
    return DEFAULT_LANGUAGE;
  }
}
