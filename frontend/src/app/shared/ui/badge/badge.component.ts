import { Component, Input, HostBinding, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'shared-badge',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './badge.component.html',
  styleUrls: ['./badge.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BadgeComponent {
  @Input() variant: 'primary' | 'secondary' | 'tertiary' | 'success' | 'danger' | 'muted' = 'primary';
  @Input() size: 'sm' | 'md' = 'md';
  @Input() tone: 'soft' | 'solid' | 'outline' = 'soft';

  @HostBinding('class') get classes() {
    return [
      'badge',
      `badge--${this.variant}`,
      `badge--${this.size}`,
      `badge--tone-${this.tone}`,
    ].join(' ');
  }
}
