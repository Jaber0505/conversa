import { Component, Input, HostBinding, ChangeDetectionStrategy } from '@angular/core';

@Component({
  selector: 'shared-card',
  standalone: true,
  templateUrl: './card.component.html',
  styleUrls: ['./card.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CardComponent {
  /** Effet visuel */
  @Input() tone: 'soft' | 'elevated' | 'ghost' = 'soft';

  /** Curseur + hover si cliquable */
  @Input() clickable = false;

  /** Padding interne (body/header/footer) */
  @Input() padded = true;

  @HostBinding('class') get cls() {
    return [
      'card',
      `card--tone-${this.tone}`,
      this.clickable ? 'card--clickable' : '',
      this.padded ? 'card--padded' : '',
    ].join(' ');
  }
}
