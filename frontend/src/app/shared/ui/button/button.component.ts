import { Component, Input, HostBinding, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'shared-button',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './button.component.html',
  styleUrls: ['./button.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ButtonComponent {
  @Input() variant: 'primary'|'outline'|'accent'|'danger' = 'primary';
  @Input() size: 'sm'|'md'|'lg' = 'md';
  @Input() block = false;
  @Input() type: 'button'|'submit'|'reset' = 'button';
  @Input() disabled = false;

  @HostBinding('attr.role') role = 'button';
  @HostBinding('class') get classes() {
    return [
      'btn',
      `btn--${this.variant}`,
      `btn--${this.size}`,
      this.block ? 'btn--block' : ''
    ].join(' ');
  }
  @HostBinding('attr.aria-disabled') get ariaDisabled() { return this.disabled ? 'true' : null; }
}
