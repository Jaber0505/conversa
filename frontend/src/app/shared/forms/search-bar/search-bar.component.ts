import { Component, EventEmitter, Input, Output, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { InputComponent } from '@shared/forms/input/input.component';
import { SelectComponent } from '@shared/forms/select/select.component';
import { ButtonComponent } from '@shared/ui/button/button.component';
import { FormFieldComponent } from '@shared/forms/form-field/form-field.component';

export type SelectOption = { value: string; label: string };

export type FilterConfig =
  | { key: string; label: string; type: 'select'; options: SelectOption[]; searchable?: boolean; placeholder?: string }
  | { key: string; label: string; type: 'boolean'; placeholder?: string };

export type GenericSearch = { q: string; filters: Record<string, string | boolean | undefined> };

@Component({
  selector: 'shared-search-bar',
  standalone: true,
  imports: [CommonModule, FormFieldComponent, InputComponent, SelectComponent, ButtonComponent],
  templateUrl: './search-bar.component.html',
  styleUrls: ['./search-bar.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SearchBarComponent {
  @Input() placeholder = 'Rechercher…';
  @Input() filters: FilterConfig[] = [];
  @Input() showAdvanced = true;

  query = '';
  advancedOpen = false;
  filterValues: Record<string, string | boolean | undefined> = {};

  @Output() search = new EventEmitter<GenericSearch>();
  @Output() advanced = new EventEmitter<boolean>();

  get hasAnyFilter(): boolean {
    if (this.query?.trim()) return true;
    return (this.filters ?? []).some(f => {
      const v = this.filterValues[f.key];
      return v !== undefined && v !== '' && v !== null;
    });
  }

  booleanOptions(): SelectOption[] {
    return [
      { value: 'true',  label: 'Oui' },
      { value: 'false', label: 'Non' },
    ];
  }

  getSelectValue(f: FilterConfig): string | undefined {
    const v = this.filterValues[f.key];
    if (f.type === 'boolean') {
      if (v === true) return 'true';
      if (v === false) return 'false';
      return undefined;
    }
    return typeof v === 'string' && v ? v : undefined;
  }

  onFilterChange(key: string, type: FilterConfig['type'], raw: string | undefined) {
    if (type === 'boolean') {
      if (raw === 'true') this.filterValues[key] = true;
      else if (raw === 'false') this.filterValues[key] = false;
      else this.filterValues[key] = undefined;
    } else {
      this.filterValues[key] = raw || undefined;
    }
  }

  submit() {
    this.search.emit({ q: this.query.trim(), filters: { ...this.filterValues } });
  }

  reset() {
    this.query = '';
    this.filterValues = {};
    this.submit();
  }

  toggleAdvanced() {
    this.advancedOpen = !this.advancedOpen;
    this.advanced.emit(this.advancedOpen);
  }

  trackByKey = (_: number, f: FilterConfig) => f.key;
}
