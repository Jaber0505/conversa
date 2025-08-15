import {
  Component, Input, Output, EventEmitter, ChangeDetectionStrategy,
  HostListener, ElementRef, inject, signal, computed
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { BadgeComponent } from '@shared/ui/badge/badge.component';

export type SelectOption = { value: string; label: string };

@Component({
  selector: 'shared-multi-select',
  standalone: true,
  imports: [CommonModule, BadgeComponent],
  templateUrl: './multi-select.component.html',
  styleUrls: ['./multi-select.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MultiSelectComponent {
  private host = inject(ElementRef<HTMLElement>);

  /* API */
  @Input() placeholder = 'Sélectionner…';
  @Input() options: SelectOption[] = [];
  @Input() disabled = false;

  // API value (string[])
  private _value = signal<string[]>([]);
  @Input() set value(v: string[] | undefined) { this._value.set(v ?? []); }
  get value(): string[] { return this._value(); }
  @Output() valueChange = new EventEmitter<string[]>();

  // API selected (Option[]) - alias de value
  @Input() set selected(opts: SelectOption[] | undefined) {
    this._value.set((opts ?? []).map(o => o.value));
  }
  get selected(): SelectOption[] {
    const set = new Set(this._value());
    return this.options.filter(o => set.has(o.value));
  }
  @Output() selectedChange = new EventEmitter<SelectOption[]>();

  /* UI state */
  isOpen = false;
  query = signal('');

  filtered = computed(() => {
    const q = this.query().trim().toLowerCase();
    if (!q) return this.options;
    return this.options.filter(o => o.label.toLowerCase().includes(q));
  });

  /* Helpers sélection */
  isChecked(val: string) { return this._value().includes(val); }

  private emitBoth() {
    this.valueChange.emit(this._value());
    this.selectedChange.emit(this.selected);
  }

  onToggle(val: string) {
    const cur = new Set(this._value());
    cur.has(val) ? cur.delete(val) : cur.add(val);
    this._value.set(Array.from(cur));
    this.emitBoth();
  }

  removeOne(val: string, ev?: MouseEvent) {
    ev?.stopPropagation();
    this._value.set(this._value().filter(v => v !== val));
    this.emitBoth();
  }

  clearAll(ev?: MouseEvent) {
    ev?.stopPropagation();
    this._value.set([]);
    this.emitBoth();
  }

  /* Recherche */
  onSearch(ev: Event) {
    const target = ev.target as HTMLInputElement | null;
    if (!target) return;
    this.query.set(target.value);
  }

  /* Ouverture/Fermeture */
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

  /* Fermer au clic extérieur + Esc */
  @HostListener('document:click', ['$event'])
  onDocumentClick(ev: MouseEvent) {
    if (!this.isOpen) return;
    const target = ev.target as Node | null;
    if (target && !this.host.nativeElement.contains(target)) this.close();
  }

  @HostListener('document:keydown.escape')
  onEsc() {
    if (this.isOpen) this.close();
  }
}
