import { Component, EventEmitter, Input, Output } from '@angular/core';
import { NgIf, NgClass } from '@angular/common';
import { FormsModule } from '@angular/forms'; // ← ajout

import {ButtonComponent as SharedButton, InputComponent, MultiSelectComponent} from '@shared';
import { TPipe } from '@core/i18n';

@Component({
  selector: 'shared-search-panel',
  standalone: true,
  imports: [FormsModule, MultiSelectComponent, InputComponent, SharedButton, TPipe, NgIf, NgClass], // ← FormsModule ici
  templateUrl: './search-panel.component.html',
  styleUrls: ['./search-panel.component.scss']
})
export class SharedSearchPanelComponent {
  @Input() labelKey = 'common.LanguageSearch';
  @Input() searchLabelKey = 'common.searchInput';
  @Input() searchPlaceholderKey = 'search.input.placeholder';

  @Input() options: { label: string; value: string }[] = [];
  @Input() value: string[] = [];

  @Input() searchInput = '';
  @Input() clearButton = true;
  @Input() compact = false;

  @Output() valueChange = new EventEmitter<string[]>();
  @Output() search = new EventEmitter<{ searchInput: string; selectedLangCodes: string[] }>();
  @Output() reset = new EventEmitter<void>();

  onCodesChange(codes: string[]) {
    this.value = codes;
    this.valueChange.emit(codes);
  }
  onSearchClick() {
    this.search.emit({ searchInput: this.searchInput, selectedLangCodes: this.value });
  }
  onResetClick() {
    this.searchInput = '';
    this.value = [];
    this.valueChange.emit(this.value);
    this.reset.emit();
  }
}


