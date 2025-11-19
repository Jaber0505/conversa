# Exemples d'Utilisation - EventActionButton

## 🎯 Exemple 1 : Liste d'événements (Simple)

```typescript
// events-list.component.ts
import { Component, signal } from '@angular/core';
import { EventActionButtonComponent } from '@shared';
import { EventAction } from '@app/features/events/services/event-actions.service';

@Component({
  selector: 'app-events-list',
  standalone: true,
  imports: [EventActionButtonComponent],
  template: `
    <div class="events-grid">
      @for (event of events(); track event.id) {
        <div class="event-card">
          <h3>{{ event.title }}</h3>
          <p>{{ event.datetime_start | date }}</p>

          <!-- Bouton d'action automatique -->
          <app-event-action-button
            [event]="event"
            [userId]="currentUserId()"
            [isOrganizer]="event.organizer_id === currentUserId()"
            (actionTriggered)="handleAction($event, event)"
          />
        </div>
      }
    </div>
  `
})
export class EventsListComponent {
  currentUserId = signal<number | null>(null);
  events = signal<EventDto[]>([]);

  handleAction(action: EventAction, event: EventDto) {
    console.log('Action:', action, 'Event:', event.id);

    switch (action) {
      case 'user-book':
        this.createBooking(event);
        break;
      case 'user-pay-booking':
        this.redirectToPayment(event);
        break;
      case 'organizer-pay-and-publish':
        this.publishEvent(event);
        break;
      default:
        console.warn('Unhandled action:', action);
    }
  }

  createBooking(event: EventDto) {
    // Logique de création de réservation
  }

  redirectToPayment(event: EventDto) {
    // Redirection vers Stripe
  }

  publishEvent(event: EventDto) {
    // Paiement et publication
  }
}
```

---

## 🎨 Exemple 2 : Page de détail (Complet)

```typescript
// event-detail.component.ts
import { Component, signal, computed } from '@angular/core';
import { EventActionButtonComponent } from '@shared';
import { EventAction } from '@app/features/events/services/event-actions.service';

@Component({
  selector: 'app-event-detail',
  standalone: true,
  imports: [EventActionButtonComponent],
  template: `
    <div class="event-detail-page">
      <!-- En-tête -->
      <h1>{{ event()?.title }}</h1>

      <!-- Informations -->
      <div class="event-info">
        <p>Date: {{ event()?.datetime_start | date }}</p>
        <p>Prix: {{ formatPrice(event()?.price_cents) }}</p>
        <p>Organisateur: {{ event()?.organizer_first_name }}</p>
      </div>

      <!-- Bouton d'action (mode multi-boutons) -->
      <div class="action-section">
        <app-event-action-button
          [event]="event()!"
          [userId]="currentUserId()"
          [isOrganizer]="isOrganizer()"
          [showBadge]="true"
          [size]="'lg'"
          [primaryOnly]="false"
          [loading]="isProcessing()"
          (actionTriggered)="handleAction($event)"
          (viewDetails)="scrollToDescription()"
        />
      </div>

      <!-- Description -->
      <div class="event-description">
        <h2>Description</h2>
        <p>{{ event()?.theme }}</p>
      </div>
    </div>
  `
})
export class EventDetailComponent {
  event = signal<EventDetailDto | null>(null);
  currentUserId = signal<number | null>(null);
  isProcessing = signal(false);

  isOrganizer = computed(() => {
    const evt = this.event();
    const userId = this.currentUserId();
    return !!(evt && userId && evt.organizer_id === userId);
  });

  handleAction(action: EventAction) {
    this.isProcessing.set(true);

    switch (action) {
      case 'user-book':
        this.bookEvent();
        break;

      case 'user-pay-booking':
        this.payBooking();
        break;

      case 'user-cancel-booking':
        this.cancelBooking();
        break;

      case 'user-join-game':
        this.joinGame();
        break;

      case 'organizer-start-game':
        this.startGame();
        break;

      case 'organizer-delete-draft':
        this.deleteDraft();
        break;

      default:
        console.warn('Action non gérée:', action);
        this.isProcessing.set(false);
    }
  }

  private bookEvent() {
    // Créer réservation + redirection Stripe
    setTimeout(() => this.isProcessing.set(false), 1000);
  }

  private payBooking() {
    // Redirection vers paiement Stripe
    setTimeout(() => this.isProcessing.set(false), 500);
  }

  private cancelBooking() {
    // Annulation avec confirmation
    if (confirm('Annuler la réservation ?')) {
      // Appel API
      setTimeout(() => this.isProcessing.set(false), 1000);
    } else {
      this.isProcessing.set(false);
    }
  }

  private joinGame() {
    // Navigation vers la page du jeu
    this.router.navigate(['/games', this.event()?.id]);
  }

  private startGame() {
    // Démarrage du jeu (organisateur)
    setTimeout(() => this.isProcessing.set(false), 1500);
  }

  private deleteDraft() {
    if (confirm('Supprimer ce brouillon ?')) {
      // Suppression
      setTimeout(() => this.isProcessing.set(false), 800);
    } else {
      this.isProcessing.set(false);
    }
  }
}
```

---

## 🎮 Exemple 3 : Intégration dans Event Card existant

```typescript
// event-card.component.ts
import { Component, Input, Output, EventEmitter } from '@angular/core';
import { EventActionButtonComponent } from '@shared';
import { EventAction } from '@app/features/events/services/event-actions.service';

@Component({
  selector: 'app-event-card',
  standalone: true,
  imports: [EventActionButtonComponent],
  template: `
    <div class="event-card" (click)="onCardClick()">
      <!-- Image -->
      <img [src]="event.photo" [alt]="event.title" />

      <!-- Contenu -->
      <div class="card-content">
        <h3>{{ event.title }}</h3>
        <p>{{ event.datetime_start | date }}</p>
        <p>{{ event.partner_name }}</p>
      </div>

      <!-- Action button (empêche propagation du click) -->
      <div class="card-actions" (click)="$event.stopPropagation()">
        <app-event-action-button
          [event]="event"
          [userId]="currentUserId"
          [isOrganizer]="isOrganizer"
          [showBadge]="true"
          [size]="'md'"
          [loading]="isPaymentLoading"
          (actionTriggered)="onAction($event)"
          (viewDetails)="onViewDetails()"
        />
      </div>
    </div>
  `,
  styles: [`
    .event-card {
      cursor: pointer;
      border: 1px solid #ddd;
      border-radius: 8px;
      overflow: hidden;
      transition: transform 0.2s;
    }

    .event-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    .card-actions {
      padding: 16px;
      border-top: 1px solid #eee;
    }
  `]
})
export class EventCardComponent {
  @Input({ required: true }) event!: EventDto;
  @Input() currentUserId: number | null = null;
  @Input() isOrganizer = false;
  @Input() isPaymentLoading = false;

  @Output() action = new EventEmitter<{ action: EventAction; event: EventDto }>();
  @Output() viewDetails = new EventEmitter<number>();

  onCardClick() {
    this.viewDetails.emit(this.event.id);
  }

  onAction(action: EventAction) {
    this.action.emit({ action, event: this.event });
  }

  onViewDetails() {
    this.viewDetails.emit(this.event.id);
  }
}
```

---

## 📅 Exemple 4 : Dans My Bookings

```typescript
// my-bookings.component.ts
import { Component, signal } from '@angular/core';
import { EventActionButtonComponent } from '@shared';
import { EventAction } from '@app/features/events/services/event-actions.service';

@Component({
  selector: 'app-my-bookings',
  standalone: true,
  imports: [EventActionButtonComponent],
  template: `
    <div class="my-bookings-page">
      <h1>Mes réservations</h1>

      @for (booking of bookings(); track booking.id) {
        <div class="booking-card">
          <div class="booking-info">
            <h3>{{ booking.event.title }}</h3>
            <p>{{ booking.event.datetime_start | date }}</p>
            <p class="status">{{ booking.status }}</p>
          </div>

          <!-- Actions contextuelles selon le statut -->
          <div class="booking-actions">
            <app-event-action-button
              [event]="booking.event"
              [userId]="currentUserId()"
              [isOrganizer]="false"
              [showBadge]="true"
              [size]="'sm'"
              (actionTriggered)="handleBookingAction($event, booking)"
            />
          </div>
        </div>
      }
    </div>
  `
})
export class MyBookingsComponent {
  currentUserId = signal<number | null>(null);
  bookings = signal<BookingWithEvent[]>([]);

  handleBookingAction(action: EventAction, booking: BookingWithEvent) {
    switch (action) {
      case 'user-pay-booking':
        this.payBooking(booking);
        break;

      case 'user-cancel-booking':
        this.confirmCancelBooking(booking);
        break;

      case 'user-join-game':
        this.navigateToGame(booking.event.id);
        break;
    }
  }

  payBooking(booking: BookingWithEvent) {
    // Créer session Stripe et rediriger
  }

  confirmCancelBooking(booking: BookingWithEvent) {
    // Modal de confirmation puis annulation
  }

  navigateToGame(eventId: number) {
    this.router.navigate(['/games', eventId]);
  }
}
```

---

## 🔧 Exemple 5 : Mode Debug (Afficher toutes les actions)

```typescript
// event-debug.component.ts
import { Component } from '@angular/core';
import { EventActionButtonComponent } from '@shared';

@Component({
  selector: 'app-event-debug',
  standalone: true,
  imports: [EventActionButtonComponent],
  template: `
    <div class="debug-panel">
      <h2>Debug Actions</h2>

      <!-- Afficher TOUTES les actions disponibles -->
      <app-event-action-button
        [event]="testEvent"
        [userId]="userId"
        [isOrganizer]="true"
        [showBadge]="true"
        [primaryOnly]="false"
        (actionTriggered)="logAction($event)"
      />

      <pre>{{ lastAction }}</pre>
    </div>
  `
})
export class EventDebugComponent {
  userId = 123;
  testEvent = {
    id: 1,
    title: 'Test Event',
    status: 'PUBLISHED',
    datetime_start: new Date().toISOString(),
    organizer_id: 123,
    game_type: 'picture_description',
    game_started: false,
    max_participants: 6,
    booked_seats: 2,
    // ... autres champs
  };

  lastAction = '';

  logAction(action: EventAction) {
    this.lastAction = JSON.stringify({ action, timestamp: new Date() }, null, 2);
    console.log('Action déclenchée:', action);
  }
}
```

---

## ✅ Bonnes Pratiques

### 1. Toujours gérer tous les types d'actions
```typescript
handleAction(action: EventAction) {
  switch (action) {
    // Organisateur
    case 'organizer-pay-and-publish':
    case 'organizer-delete-draft':
    case 'organizer-cancel-event':
    case 'organizer-start-game':
    case 'organizer-join-game':
      // ...
      break;

    // Utilisateur
    case 'user-book':
    case 'user-pay-booking':
    case 'user-cancel-booking':
    case 'user-join-game':
      // ...
      break;

    default:
      console.warn('Action non gérée:', action);
  }
}
```

### 2. Utiliser l'état de chargement
```typescript
async handleAction(action: EventAction) {
  this.loading.set(true);

  try {
    await this.performAction(action);
  } catch (error) {
    console.error('Erreur:', error);
    alert('Une erreur est survenue');
  } finally {
    this.loading.set(false);
  }
}
```

### 3. Empêcher la propagation dans les cards cliquables
```html
<div class="event-card" (click)="viewDetails()">
  <!-- Contenu... -->

  <div (click)="$event.stopPropagation()">
    <app-event-action-button
      [event]="event"
      (actionTriggered)="handleAction($event)"
    />
  </div>
</div>
```

### 4. Utiliser computed pour isOrganizer
```typescript
isOrganizer = computed(() => {
  const evt = this.event();
  const userId = this.currentUserId();
  return !!(evt && userId && evt.organizer_id === userId);
});
```
