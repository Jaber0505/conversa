import { ChangeDetectorRef, DestroyRef, Pipe, PipeTransform, inject } from '@angular/core';
import { I18nService } from './i18n.service';
import { LangService } from './lang.service';

@Pipe({ name: 't', standalone: true, pure: false })
export class TPipe implements PipeTransform {
  private readonly i18n = inject(I18nService);
  private readonly lang = inject(LangService);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly destroyRef = inject(DestroyRef);

  private lastLang?: string;
  private lastKey?: string;
  private lastParamsKey?: string;
  private lastResult?: string;

  constructor() {
    const sub = this.i18n.ready$.subscribe(() => {
      this.invalidate();
      this.cdr.markForCheck();
    });
    this.destroyRef.onDestroy(() => sub.unsubscribe());
  }

  transform(key: string, params?: Record<string, any>): string {
    const currentLang = this.lang.current;
    const paramsKey = params ? stableStringify(params) : '';

    if (
      this.lastLang === currentLang &&
      this.lastKey === key &&
      this.lastParamsKey === paramsKey &&
      this.lastResult !== undefined
    ) {
      return this.lastResult;
    }

    const res = this.i18n.t(key, params);
    this.lastLang = currentLang;
    this.lastKey = key;
    this.lastParamsKey = paramsKey;
    this.lastResult = res;
    return res;
  }

  private invalidate() {
    this.lastLang = this.lastKey = this.lastParamsKey = undefined;
    this.lastResult = undefined;
  }
}

function stableStringify(obj: Record<string, any>): string {
  const keys = Object.keys(obj).sort();
  const out: Record<string, any> = {};
  for (const k of keys) out[k] = obj[k];
  return JSON.stringify(out);
}
