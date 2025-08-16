import { Component, EventEmitter, Input, Output, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TPipe } from '@core/i18n'; // <- pipe de traduction

export type Lang = 'fr' | 'en' | 'nl';

@Component({
  standalone: true,
  selector: 'app-language-popover',
  imports: [CommonModule, TPipe], // <- important pour | t
  templateUrl: './language-popover.component.html',
  styleUrls: ['./language-popover.component.scss']
})
export class LanguagePopoverComponent implements OnChanges {
  @Input() langs: ReadonlyArray<Lang> = ['fr', 'en', 'nl'] as const;
  @Input() current: Lang = 'fr';

  @Output() save = new EventEmitter<Lang>();
  @Output() close = new EventEmitter<void>();

  private _selected: Lang = this.current;

  ngOnChanges(_: SimpleChanges): void {
    this._selected = this.current;
  }

  selected(): Lang {
    return this._selected;
  }

  onToggle(next: Lang) {
    this._selected = next;
  }

  onConfirm() {
    this.save.emit(this._selected);
  }

  onCancel() {
    this.close.emit();
  }

  // Retourne la clé i18n du nom de langue
  labelKeyOf(l: Lang): string {
    return `languages.${l}`;
  }

  // Optionnel: clé du titre
  titleKey(): string {
    return 'common.lang_change';
  }
}
