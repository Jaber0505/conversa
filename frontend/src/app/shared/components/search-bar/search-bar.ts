import { Component, input, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MultiSelectComponent } from '../../forms/multi-select/multi-select.component';
import { ButtonComponent } from '../../ui/button/button.component';

export interface SearchBarField {
  type: 'multiselect' | 'text';
  placeholder?: string;
  options?: { value: string; label: string }[];
  value?: string | string[];
  width?: string; // e.g., '200px', '1fr', '300px'
}

@Component({
  selector: 'shared-search-bar',
  standalone: true,
  imports: [CommonModule, FormsModule, MultiSelectComponent, ButtonComponent],
  templateUrl: './search-bar.html',
  styleUrls: ['./search-bar.scss'],
})
export class SearchBarComponent {
  // Configuration des champs de recherche
  fields = input<SearchBarField[]>([]);

  // Texte du bouton de recherche
  searchButtonText = input<string>('Rechercher');

  // Événements
  search = output<Record<string, string | string[]>>();

  // État local des champs
  fieldValues: Record<number, string | string[]> = {};

  onSearch(): void {
    const values: Record<string, string | string[]> = {};
    this.fields().forEach((field, index) => {
      values[`field${index}`] = this.fieldValues[index] || (field.type === 'multiselect' ? [] : '');
    });
    this.search.emit(values);
  }

  onFieldChange(index: number, value: string | string[]): void {
    this.fieldValues[index] = value;
  }

  // Helpers to provide strongly-typed values to the template
  getMultiValue(index: number): string[] {
    const v = this.fieldValues[index];
    return Array.isArray(v) ? (v as string[]) : [];
  }

  getTextValue(index: number): string {
    const v = this.fieldValues[index];
    return typeof v === 'string' ? v : '';
  }

  getGridTemplate(): string {
    const fields = this.fields();
    if (fields.length === 0) return '1fr auto';

    const widths = fields.map(f => f.width || '1fr').join(' ');
    return `${widths} auto`;
  }
}
