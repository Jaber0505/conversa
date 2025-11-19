import { Component, Input, Output, EventEmitter, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TPipe } from '@core/i18n';
import { EventDto } from '@core/models';
import { PriorityBadge } from '../../services/events-sorting.service';
import { CurrencyFormatterService, DateFormatterService } from '@app/core/services';
import { CardComponent, BadgeComponent, EventActionButtonComponent } from '@shared';
import { EventAction } from '../../services/event-actions.service';

@Component({
  selector: 'app-event-card',
  standalone: true,
  imports: [CommonModule, TPipe, CardComponent, BadgeComponent, EventActionButtonComponent],
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
  @Input() priorityBadge: PriorityBadge | null = null;
  @Input() userId: number | null = null; // ID de l'utilisateur connecté

  @Output() book = new EventEmitter<number>();
  @Output() viewDetails = new EventEmitter<number>();
  @Output() payDraft = new EventEmitter<number>();
  @Output() playGame = new EventEmitter<number>();

  get isDraft(): boolean {
    return this.event.status === 'DRAFT';
  }

  get isPublished(): boolean {
    return this.event.status === 'PUBLISHED';
  }

  get canPlayGame(): boolean {
    // Vérifier si l'événement a un jeu configuré, est publié, et a commencé
    if (!this.event.game_type || this.event.status !== 'PUBLISHED') {
      return false;
    }

    const now = new Date();
    const eventStart = new Date(this.event.datetime_start);
    const hasStarted = now >= eventStart;

    // Si organisateur et jeu pas encore démarré, peut lancer le jeu
    if (this.isOrganizer && hasStarted && !this.event.game_started) {
      return true;
    }

    // Si participant et jeu démarré, peut rejoindre
    if (!this.isOrganizer && this.event.game_started) {
      return true;
    }

    return false;
  }

  get formattedDate(): string {
    return this.dateFormatter.formatDateTime(this.event.datetime_start);
  }

  get formattedPrice(): string {
    if (this.event.price_cents === 0) return 'Gratuit';
    return this.currencyFormatter.formatEUR(this.event.price_cents ?? 0);
  }

  get partnerAddress(): string {
    return this.event.partner_address || this.event.address;
  }

  get languageBadgeKey(): string {
    const code = (this.event.language_code || '').toLowerCase();
    return code ? `languages.${code}` : 'common.language';
  }

  get interestBadgeKey(): string | null {
    if (this.priorityBadgeLabel) return this.priorityBadgeLabel;
    if (this.isRecommended) return 'events.recommended';
    if (this.isNearby) return 'events.nearby';
    return null;
  }

  get isDisabled(): boolean {
    return this.event.is_cancelled || this.event.alreadyBooked || this.isFull;
  }

  get isFull(): boolean {
    const fullFlag = (this.event as any).is_full;
    if (typeof fullFlag === 'boolean') {
      return fullFlag;
    }
    const max = this.event.max_participants || 0;
    if (!max) return false;
    const current =
      (this.event as any).booked_seats ??
      this.event.registration_count ??
      0;
    return current >= max;
  }

  get priorityBadgeLabel(): string | null {
    switch (this.priorityBadge) {
      case 'recommended':
        return 'events.badges.recommended';
      case 'full':
        return 'events.badges.full';
      case 'cancelled':
        return 'events.badges.cancelled';
      default:
        return null;
    }
  }

  get priorityBadgeVariant(): 'accent' | 'primary' | 'success' | 'muted' | 'danger' | 'secondary' | 'tertiary' {
    switch (this.priorityBadge) {
      case 'recommended':
        return 'accent';
      case 'full':
      case 'cancelled':
        return 'danger';
      default:
        return 'accent';
    }
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

  onPlayGame(event?: Event): void {
    if (event) {
      event.stopPropagation();
    }
    this.playGame.emit(this.event.id);
  }

  handleEventAction(action: EventAction): void {
    // Mapper les actions du EventActionButton vers les outputs existants
    // L'action est une string directe (EventAction type)
    switch (action) {
      case 'view-details':
        this.viewDetails.emit(this.event.id);
        break;
      case 'organizer-pay-and-publish':
        this.payDraft.emit(this.event.id);
        break;
      case 'organizer-start-game':
      case 'organizer-join-game':
      case 'user-join-game':
        this.playGame.emit(this.event.id);
        break;
      case 'user-book':
        this.book.emit(this.event.id);
        break;
      case 'user-pay-booking':
        this.payDraft.emit(this.event.id);
        break;
      case 'user-cancel-booking':
      case 'organizer-cancel-event':
        // Ces actions nécessitent une confirmation, on navigue vers les détails
        this.viewDetails.emit(this.event.id);
        break;
      case 'organizer-delete-draft':
        // Cette action nécessite une confirmation, on navigue vers les détails
        this.viewDetails.emit(this.event.id);
        break;
    }
  }
}
