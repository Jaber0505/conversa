import { Component, Input, HostBinding, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'shared-button',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './button.component.html',
  styleUrls: ['./button.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ButtonComponent {
  @Input() variant: 'primary'|'outline'|'accent'|'danger'|'link' = 'primary';
  @Input() size: 'sm'|'md'|'lg' = 'md';
  @Input() block = false;
  @Input() type: 'button'|'submit'|'reset' = 'button';
  @Input() disabled = false;

  // Router support (forward router inputs to inner button)
  @Input() routerLink?: string | any[];
  @Input() queryParams?: Record<string, any>;
  @Input() fragment?: string;
  @Input() state?: any;
  @Input() queryParamsHandling?: 'merge' | 'preserve' | '';
  @Input() replaceUrl?: boolean;
  @Input() skipLocationChange?: boolean;

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
