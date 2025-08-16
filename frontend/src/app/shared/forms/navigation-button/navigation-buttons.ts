import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ButtonComponent } from '@shared/ui/button/button.component';
import { TPipe } from '@core/i18n';

type Align = 'start' | 'center' | 'end' | 'between';

@Component({
  selector: 'navigation-buttons', // ou 'shared-navigation-buttons' si tu préfères
  standalone: true,
  imports: [CommonModule, ButtonComponent, TPipe],
  templateUrl: './navigation-buttons.html',
  styleUrls: ['./navigation-buttons.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NavigationButtonsComponent {
  // Visibilité
  @Input() showPrev = true;
  @Input() showNext = true;

  // Labels (i18n-ready)
  @Input() prevLabel = 'common.prev';
  @Input() nextLabel = 'common.next';

  // Variantes / tailles
  @Input() prevVariant: 'primary'|'outline'|'accent'|'danger' = 'outline';
  @Input() nextVariant: 'primary'|'outline'|'accent'|'danger' = 'primary';
  @Input() size: 'sm'|'md' = 'md';
  @Input() block = false;

  // Disabled
  @Input() prevDisabled = false;
  @Input() nextDisabled = false;

  // Alignement
  @Input() align: Align = 'between';

  // A11y
  @Input() ariaLabel = 'Navigation';

  // Events
  @Output() prevClick = new EventEmitter<void>();
  @Output() nextClick = new EventEmitter<void>();

  onPrev() { if (!this.prevDisabled) this.prevClick.emit(); }
  onNext() { if (!this.nextDisabled) this.nextClick.emit(); }

  get alignClass() {
    return `nav--${this.align}` + (this.block ? ' nav--block' : '');
  }
}
