import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { DOCUMENT } from '@angular/common';
import { LangService } from './lang.service';
import { DEFAULT_LANGUAGE, type Lang } from './languages.config';
import { BehaviorSubject, distinctUntilChanged, switchMap, from, firstValueFrom } from 'rxjs';

type Dict = Record<string, any>;

@Injectable({ providedIn: 'root' })
export class I18nService {
  private readonly http = inject(HttpClient);
  private readonly lang = inject(LangService);
  private readonly document = inject(DOCUMENT);

  private cache = new Map<Lang, Dict>();

  private readySubject = new BehaviorSubject<boolean>(false);
  readonly ready$ = this.readySubject.asObservable();
  readonly changed$ = this.ready$; // compat: utilisé par TPipe/TAttr

  constructor() {
    this.lang.lang$
      .pipe(
        distinctUntilChanged(),
        switchMap((l) => from(this.ensureLoaded(l)))
      )
      .subscribe(() => this.readySubject.next(true));
  }

  /** Traduction avec fallback fr + interpolation {{var}} */
  t(key: string, params?: Record<string, string | number>): string {
    const cur = this.cache.get(this.lang.current) ?? {};
    const fr = this.cache.get(DEFAULT_LANGUAGE) ?? {};
    const raw = (getByPath(cur, key) ?? getByPath(fr, key) ?? key) as string;
    return interpolate(raw, params);
  }

  /** Précharge la langue courante + fr au bootstrap */
  async preload(lang?: Lang): Promise<void> {
    const target = (lang as Lang) ?? DEFAULT_LANGUAGE;
    const needDefault = target !== DEFAULT_LANGUAGE;
    const tasks: Promise<void>[] = [];
    if (!this.cache.has(target)) tasks.push(this.loadLang(target));
    if (needDefault && !this.cache.has(DEFAULT_LANGUAGE)) tasks.push(this.loadLang(DEFAULT_LANGUAGE));
    if (tasks.length) await Promise.all(tasks);
  }

  private ensureLoaded(l: Lang): Promise<void> {
    const needDefault = l !== DEFAULT_LANGUAGE && !this.cache.has(DEFAULT_LANGUAGE);
    const tasks: Promise<void>[] = [];
    if (!this.cache.has(l)) tasks.push(this.loadLang(l));
    if (needDefault) tasks.push(this.loadLang(DEFAULT_LANGUAGE));
    return tasks.length ? Promise.all(tasks).then(() => {}) : Promise.resolve();
  }

  private async loadLang(l: Lang): Promise<void> {
    const base = this.document.baseURI; // Récupère le <base href="..."> du index.html
    // Ajout d’un timestamp pour éviter le cache navigateur après déploiement
    const url = new URL(`assets/i18n/${l}.json?v=${Date.now()}`, base).toString();
    const data = await firstValueFrom(this.http.get<Dict>(url));
    this.cache.set(l, data ?? {});
  }
}

/* Helpers */
function getByPath(obj: any, path: string): any {
  return path.split('.').reduce((acc, k) => (acc && k in acc ? acc[k] : undefined), obj);
}

function interpolate(template: string, params?: Record<string, string | number>): string {
  if (!params) return template;
  return template.replace(/\{\{\s*(\w+)\s*\}\}/g, (_, k) => String(params[k] ?? ''));
}
