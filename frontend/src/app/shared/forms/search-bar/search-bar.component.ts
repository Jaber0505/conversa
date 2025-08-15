import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormFieldComponent } from '@shared/forms/form-field/form-field.component';
import { InputComponent } from '@shared/forms/input/input.component';
import { SelectComponent } from '@shared/forms/select/select.component';
import { BadgeComponent, ButtonComponent } from '@shared/ui';

type Option = { value: string; label: string };
type SearchPayload = { q?: string; lang?: string; area?: string };

@Component({
  selector: 'shared-search-bar',
  standalone: true,
  imports: [
    CommonModule,
    FormFieldComponent,
    InputComponent,
    SelectComponent,
    ButtonComponent,
    BadgeComponent,
  ],
  templateUrl: './search-bar.component.html',
  styleUrls: ['./search-bar.component.scss'],
})
export class SearchBarComponent {
  @Input() placeholder = 'Rechercher un événement…';
  @Input() langs: Option[] = [];
  @Input() areas: Option[] = [];
  @Output() search = new EventEmitter<SearchPayload>();

  q = '';
  lang?: string;
  area?: string;

  advancedOpen = false;

  get hasAnyFilter() {
    return !!(this.q?.trim() || this.lang || this.area);
  }

  toggleAdvanced() { this.advancedOpen = !this.advancedOpen; }

  clearAll() {
    this.q = '';
    this.lang = undefined;
    this.area = undefined;
  }

  clearOne(key: 'q'|'lang'|'area') {
    if (key === 'q') this.q = '';
    if (key === 'lang') this.lang = undefined;
    if (key === 'area') this.area = undefined;
  }

  onSubmit(e: Event) {
    e.preventDefault();
    this.search.emit({
      q: this.q?.trim() || undefined,
      lang: this.lang || undefined,
      area: this.area || undefined,
    });
  }

  displayLabel(options: Option[], value?: string) {
    return options.find(o => o.value === value)?.label ?? value;
  }
}
