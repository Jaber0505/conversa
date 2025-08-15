import { Directive, Input, ElementRef, Renderer2, DestroyRef, OnChanges, SimpleChanges, inject } from '@angular/core';
import { I18nService } from '@core/i18n';

type TParams = Record<string, any>;
type TValue = string | [string, TParams];
type TMap = Record<string, TValue>;

const ALLOWED_ATTRS = new Set([
  'title', 'placeholder', 'alt', 'value', 'aria-label', 'aria-description', 'aria-placeholder', 'aria-role', 'aria-roledescription'
]);

@Directive({
  selector: '[tAttr]',
  standalone: true,
})
export class TAttrDirective implements OnChanges {
  @Input('tAttr') map!: TMap;

  private readonly i18n = inject(I18nService);
  private readonly el = inject<ElementRef<HTMLElement>>(ElementRef);
  private readonly r = inject(Renderer2);
  private readonly destroyRef = inject(DestroyRef);

  constructor() {
    const sub = this.i18n.changed$.subscribe(() => this.apply());
    this.destroyRef.onDestroy(() => sub.unsubscribe());
  }

  ngOnChanges(changes: SimpleChanges): void {
    if ('map' in changes) this.apply();
  }

  private apply(): void {
    if (!this.map || typeof this.map !== 'object') return;

    for (const [attr, spec] of Object.entries(this.map)) {
      // Autorise tout ce qui est aria-* + les attrs whitelists
      if (!ALLOWED_ATTRS.has(attr) && !attr.startsWith('aria-')) continue;

      const [key, params] = Array.isArray(spec) ? spec as [string, TParams] : [spec as string, undefined];
      const value = this.i18n.t(key, params);
      this.r.setAttribute(this.el.nativeElement, attr, String(value));
    }
  }
}
