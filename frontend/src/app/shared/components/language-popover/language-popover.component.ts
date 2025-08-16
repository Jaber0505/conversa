import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output, OnChanges, SimpleChanges, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SHARED_IMPORTS } from '@shared';

export type Lang = 'FR' | 'EN' | 'NL';

@Component({
  selector: 'app-language-popover',
  standalone: true,
  imports: [CommonModule, ...SHARED_IMPORTS],
  templateUrl: './language-popover.component.html',
  styleUrls: ['./language-popover.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LanguagePopoverComponent implements OnChanges {
  @Input() langs: Lang[] = ['FR','EN','NL'];
  @Input() current: Lang = 'FR';

  @Output() save  = new EventEmitter<Lang>();
  @Output() close = new EventEmitter<void>();

  selected = signal<Lang>(this.current);

  langLabel: Record<Lang, string> = {
    FR: 'Français',
    EN: 'English',
    NL: 'Nederlands',
  };

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['current']?.currentValue) this.selected.set(changes['current'].currentValue as Lang);
  }

  onToggle(lang: Lang) { this.selected.set(lang); }           // sélection unique (type checkbox)
  onConfirm()          { this.save.emit(this.selected()); }
  onCancel()           { this.close.emit(); }
  onOverlayClick(ev: MouseEvent) {
    if ((ev.target as HTMLElement).classList.contains('lang-overlay')) this.onCancel();
  }
}
