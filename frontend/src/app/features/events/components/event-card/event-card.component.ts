import { Component, Input, Output, EventEmitter, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TPipe } from '@core/i18n';
import { EventDto } from '@core/models';
import { CurrencyFormatterService, DateFormatterService } from '@app/core/services';
import { CardComponent, BadgeComponent, ButtonComponent } from '@shared';

@Component({
  selector: 'app-event-card',
  standalone: true,
  imports: [CommonModule, TPipe, CardComponent, BadgeComponent, ButtonComponent],
  templateUrl: './event-card.component.html',
  styleUrls: ['./event-card.component.scss']
})
export class EventCardComponent {
  private readonly currencyFormatter = inject(CurrencyFormatterService);
  private readonly dateFormatter = inject(DateFormatterService);

  @Input({ required: true }) event!: EventDto;
  @Input() isNearby = false;
  @Input() isRecommended = false;
  @Input() isOrganizer = false;
  @Input() reserved = false; // for non-organizer view
  @Input() showBookButton = false; // control visibility of book button (user list)
  @Input() isPaymentLoading = false; // loading state for payment button

  @Output() book = new EventEmitter<number>();
  @Output() viewDetails = new EventEmitter<number>();
  @Output() payDraft = new EventEmitter<number>();

  get isDraft(): boolean {
    return this.event.status === 'DRAFT';
  }

  get isPublished(): boolean {
    return this.event.status === 'PUBLISHED';
  }

  get formattedDate(): string {
    return this.dateFormatter.formatDateTime(this.event.datetime_start);
  }

  get formattedPrice(): string {
    if (this.event.price_cents === 0) return 'Gratuit';
    return this.currencyFormatter.formatEUR(this.event.price_cents ?? 0);
  }

  get isDisabled(): boolean {
    return this.event.is_cancelled || this.event.alreadyBooked || false;
  }

  onBook(): void {
    if (!this.isDisabled) {
      this.book.emit(this.event.id);
    }
  }

  onViewDetails(event?: Event): void {
    if (event) {
      event.stopPropagation();
    }
    this.viewDetails.emit(this.event.id);
  }

  onCardClick(): void {
    this.viewDetails.emit(this.event.id);
  }

  onPayDraft(event?: Event): void {
    if (event) {
      event.stopPropagation();
    }
    this.payDraft.emit(this.event.id);
  }
}
