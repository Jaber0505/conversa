import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TPipe } from '@core/i18n';
import { CardComponent, ButtonComponent, BadgeComponent } from '@shared';
import type {Booking, EventDto} from '@core/models';
import { CurrencyFormatterService, DateFormatterService } from '@app/core/services';

@Component({
  selector: 'app-booking-detail',
  standalone: true,
  imports: [CommonModule, TPipe, CardComponent, ButtonComponent, BadgeComponent],
  templateUrl: './booking-detail.component.html',
  styleUrls: ['./booking-detail.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BookingDetailModalComponent {
  private readonly currencyFormatter = inject(CurrencyFormatterService);
  private readonly dateFormatter = inject(DateFormatterService);

  @Input({ required: true }) booking!: Booking;
  @Input({ required: true }) eventDto!: EventDto;

  @Input() asModal = true;
  @Input() titleKey = 'bookings.detail.title';

  @Output() close = new EventEmitter<void>();

  onClose() { this.close.emit(); }

  statusVariant(b: Booking): 'accent' | 'danger' | 'muted' {
    if (b.status === 'confirmed') return 'accent';
    if (b.status === 'cancelled_user') return 'danger';
    return 'muted';
  }

  dateLabel(iso: string): string {
    return this.dateFormatter.formatDateTime(iso);
  }

  price(cents?: number, seats?: number): string | null {
    return this.currencyFormatter.formatEURWithMultiplier(cents, seats);
  }
}
