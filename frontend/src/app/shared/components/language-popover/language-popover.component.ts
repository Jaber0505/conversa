import { Component, EventEmitter, Input, Output, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TPipe } from '@core/i18n'; // <- pipe de traduction

export type Lang = 'fr' | 'en' | 'nl';

@Component({
  standalone: true,
  selector: 'app-language-popover',
  imports: [CommonModule, TPipe],
  templateUrl: './language-popover.component.html',
  styleUrls: ['./language-popover.component.scss']
})
export class LanguagePopoverComponent implements OnChanges {
  @Input() langs: ReadonlyArray<Lang> = ['fr', 'en', 'nl'] as const;
  @Input() current: Lang = 'fr';
  @Input() allowMulti = false;
  @Input() preferred: Lang[] = [];

  @Output() save = new EventEmitter<Lang>();
  @Output() saveMulti = new EventEmitter<Lang[]>();
  @Output() close = new EventEmitter<void>();

  private _selected: Lang = this.current;
  private _prefs = new Set<Lang>();

  ngOnChanges(_: SimpleChanges): void {
    this._selected = this.current;
    this._prefs = new Set(this.preferred ?? []);
  }

  selected(): Lang {
    return this._selected;
  }

  onToggle(next: Lang) {
    this._selected = next;
  }

  onTogglePref(lang: Lang) {
    if (this._prefs.has(lang)) this._prefs.delete(lang);
    else this._prefs.add(lang);
  }

  onConfirm() {
    this.save.emit(this._selected);
    if (this.allowMulti) this.saveMulti.emit(Array.from(this._prefs));
  }

  onCancel() {
    this.close.emit();
  }

  labelKeyOf(l: Lang): string {
    return `languages.${l}`;
  }

  titleKey(): string {
    return 'common.lang_change';
  }

  isPref(l: Lang): boolean { return this._prefs.has(l); }

  flagOf(l: Lang): string {
    // Emoji flags: FR, GB (for EN), NL
    return l === 'fr' ? '🇫🇷' : l === 'en' ? '🇬🇧' : '🇳🇱';
  }
}
