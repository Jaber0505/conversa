import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { I18nService } from '@app/core/i18n/i18n.service';

export type Lang = 'fr' | 'en' | 'nl';

@Component({
  selector: 'app-lang-modal',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './lang-modal.component.html',
  styleUrls: ['./lang-modal.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LangModalComponent {
  private readonly i18n = inject(I18nService);

  @Input({ required: true }) current!: Lang;
  @Input({ required: true }) langs!: Lang[];

  @Output() close = new EventEmitter<void>();
  @Output() save = new EventEmitter<Lang>();

  selected = signal<Lang | null>(null);

  ngOnInit() { this.selected.set(this.current); }

  t(key: string) { return this.i18n.t(key); }

  onBackdrop(e: MouseEvent) {
    if (e.target && (e.target as HTMLElement).classList.contains('modal-backdrop')) {
      this.close.emit();
    }
  }
}
