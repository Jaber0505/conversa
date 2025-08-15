import { Directive, Input, ElementRef, Renderer2, DestroyRef, OnChanges, SimpleChanges, inject, SecurityContext } from '@angular/core';
import { DomSanitizer } from '@angular/platform-browser';
import { LangService, I18nService } from '@core/i18n';

type Params = Record<string, any>;

@Directive({
  selector: '[tHtml]',
  standalone: true,
})
export class THtmlDirective implements OnChanges {
  @Input('tHtml') key!: string;
  @Input() tHtmlParams?: Params;

  private readonly i18n = inject(I18nService);
  private readonly lang = inject(LangService);
  private readonly el = inject<ElementRef<HTMLElement>>(ElementRef);
  private readonly r = inject(Renderer2);
  private readonly sanitizer = inject(DomSanitizer);
  private readonly destroyRef = inject(DestroyRef);

  private lastLang?: string;
  private lastKey?: string;
  private lastParamsStr?: string;
  private lastHtml?: string;

  constructor() {
    const sub = this.i18n.ready$.subscribe(() => this.apply());
    this.destroyRef.onDestroy(() => sub.unsubscribe());
  }

  ngOnChanges(changes: SimpleChanges): void {
    if ('key' in changes || 'tHtmlParams' in changes) this.apply();
  }

  private apply(): void {
    if (!this.key) return;

    const curLang = this.lang.current;
    const paramsStr = this.tHtmlParams ? stableStringify(this.tHtmlParams) : '';

    if (this.lastLang === curLang && this.lastKey === this.key && this.lastParamsStr === paramsStr) return;

    const raw = this.i18n.t(this.key, this.tHtmlParams);
    const safe = this.sanitizer.sanitize(SecurityContext.HTML, raw) ?? '';

    if (safe !== this.lastHtml) {
      this.r.setProperty(this.el.nativeElement, 'innerHTML', safe);
      this.lastHtml = safe;
    }
    this.lastLang = curLang;
    this.lastKey = this.key;
    this.lastParamsStr = paramsStr;
  }
}

function stableStringify(obj: Record<string, any>): string {
  const k = Object.keys(obj).sort(); const o: Record<string, any> = {};
  for (const key of k) o[key] = obj[key];
  return JSON.stringify(o);
}
