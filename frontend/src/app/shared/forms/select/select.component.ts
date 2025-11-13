import {
  Component, Input, Output, EventEmitter, ChangeDetectionStrategy,
  HostListener, ElementRef, inject, signal, computed
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { I18nService, LangService } from '@core/i18n';
import { toSignal } from '@angular/core/rxjs-interop';

export type SelectOption = { value: string; label: string };

@Component({
  selector: 'shared-select',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './select.component.html',
  styleUrls: ['./select.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SelectComponent {
  private host = inject(ElementRef<HTMLElement>);
  private readonly i18n = inject(I18nService);
  private readonly lang = inject(LangService);
  private readonly currentLang = toSignal(this.lang.lang$, { initialValue: this.lang.current });

  readonly defaultPlaceholder = computed(() => {
    this.currentLang();
    return this.i18n.t('common.select.placeholder');
  });

  readonly searchPlaceholder = computed(() => {
    this.currentLang();
    return this.i18n.t('common.select.search_placeholder');
  });

  readonly clearLabel = computed(() => {
    this.currentLang();
    return this.i18n.t('common.select.clear');
  });

  readonly noResultsLabel = computed(() => {
    this.currentLang();
    return this.i18n.t('common.select.no_results');
  });

  @Input() id?: string;
  @Input() placeholder = '';
  @Input() options: SelectOption[] = [];
  @Input() disabled = false;
  @Input() searchable = true;

  private _value = signal<string | undefined>(undefined);
  @Input() set value(v: string | undefined) { this._value.set(v); }
  get value() { return this._value(); }

  @Output() valueChange = new EventEmitter<string | undefined>();

  isOpen = false;
  query = signal('');

  selectedOption = computed(() =>
    this.options.find(o => o.value === this._value())
  );

  filtered = computed(() => {
    const q = this.query().trim().toLowerCase();
    if (!q) return this.options;
    return this.options.filter(o => o.label.toLowerCase().includes(q));
  });

  toggleOpen(ev?: MouseEvent) {
    if (this.disabled) return;
    ev?.stopPropagation();
    if (!this.isOpen) {
      this.query.set('');
      this.isOpen = true;
    } else {
      this.close();
    }
  }

  close() {
    this.isOpen = false;
    this.query.set('');
  }

  onSearch(ev: Event) {
    const t = ev.target as HTMLInputElement | null;
    if (!t) return;
    this.query.set(t.value);
  }

  pick(val: string) {
    this._value.set(val);
    this.valueChange.emit(val);
    this.close();
  }

  clear(ev?: MouseEvent) {
    ev?.stopPropagation();
    this._value.set(undefined);
    this.valueChange.emit(undefined);
  }

  @HostListener('document:click', ['$event'])
  onDocClick(ev: MouseEvent) {
    if (!this.isOpen) return;
    const target = ev.target as Node | null;
    if (target && !this.host.nativeElement.contains(target)) this.close();
  }

  @HostListener('document:keydown.escape')
  onEsc() { if (this.isOpen) this.close(); }
}


