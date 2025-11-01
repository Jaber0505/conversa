import { ChangeDetectionStrategy, Component, EventEmitter, HostBinding, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ButtonComponent } from '@shared/ui/button/button.component';

@Component({
  selector: 'shared-empty-state',
  standalone: true,
  imports: [CommonModule, ButtonComponent],
  templateUrl: './empty-state.component.html',
  styleUrls: ['./empty-state.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EmptyStateComponent {
  @Input() title = '';
  @Input() subtitle?: string;
  @Input() icon?: string; // e.g. "🔎" | "📭"
  @Input() size: 'sm' | 'md' | 'lg' = 'md';
  @Input() actionLabel?: string | null;
  @Input() actionLink?: string | any[];
  @Output() action = new EventEmitter<void>();

  @HostBinding('class') get classes() {
    return ['empty', `empty--${this.size}`].join(' ');
  }
}
