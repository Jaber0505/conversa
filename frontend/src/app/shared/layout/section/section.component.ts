import { Component, Input, HostBinding, ChangeDetectionStrategy } from '@angular/core';

@Component({
  selector: 'shared-section',
  standalone: true,
  templateUrl: './section.component.html',
  styleUrls: ['./section.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SectionComponent {
  /** sm | md | lg : padding vertical */
  @Input() spacing: 'sm' | 'md' | 'lg' = 'md';
  /** rôle visuel: default | subtle (fond clair) */
  @Input() tone: 'default' | 'subtle' = 'default';
  /** id de titre (ARIA) si la section est labellisée par un heading externe */
  @Input() labelledBy?: string;

  @HostBinding('attr.role') role = 'region';
  @HostBinding('attr.aria-labelledby') get ariaLabelledBy() { return this.labelledBy || null; }
  @HostBinding('class') get classes() {
    return [`section--${this.spacing}`, `section--tone-${this.tone}`].join(' ');
  }
}
