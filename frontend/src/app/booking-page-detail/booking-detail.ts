import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TPipe } from '@core/i18n';
import { CardComponent, ButtonComponent, BadgeComponent } from '@shared';
import type { Booking } from '@core/models';

@Component({
  selector: 'app-booking-detail',
  standalone: true,
  imports: [CommonModule, TPipe, CardComponent, ButtonComponent, BadgeComponent],
  templateUrl: './booking-detail.html',
  styleUrls: ['./booking-detail.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BookingDetailModalComponent {
  @Input({ required: true }) booking!: Booking;

  @Input() asModal = true;
  @Input() titleKey = 'bookings.detail.title';
  @Input() closeKey = 'common.close';

  @Output() close = new EventEmitter<void>();

  onClose() { this.close.emit(); }

  statusVariant(b: Booking): 'accent' | 'danger' | 'muted' {
    if (b.status === 'confirmed') return 'accent';
    if (b.status === 'cancelled_user') return 'danger';
    return 'muted';
  }

  dateLabel(iso: string): string {
    try {
      return new Intl.DateTimeFormat('fr-BE', {
        weekday: 'short', day: '2-digit', month: 'short',
        hour: '2-digit', minute: '2-digit',
      }).format(new Date(iso));
    } catch { return iso; }
  }

  price(cents?: number, seats?: number): string | null {
    if (cents == null) return null;
    const total = (seats ?? 1) * cents;
    if (total === 0) return 'Gratuit';
    return new Intl.NumberFormat('fr-BE', { style: 'currency', currency: 'EUR' })
      .format(total / 100);
  }
}
