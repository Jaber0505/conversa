# EventActionButton Component

Composant réutilisable pour gérer les actions d'événements de manière intelligente et contextuelle.

## 🎯 Fonctionnalités

- ✅ **Logique métier centralisée** : Toute la logique de détermination des actions disponibles est dans `EventActionsService`
- ✅ **Désactivation automatique** : Les boutons se désactivent automatiquement selon le contexte
- ✅ **Badges d'état** : Affichage automatique des badges (Complet, Annulé, En direct, etc.)
- ✅ **Tooltips explicatifs** : Messages clairs expliquant pourquoi un bouton est désactivé
- ✅ **Multi-rôles** : Gestion des actions organisateur vs participant
- ✅ **Multi-langues** : Traductions complètes (FR, EN, NL)
- ✅ **Adaptation contextuelle** : Le bouton s'adapte selon l'état de l'événement et de l'utilisateur

## 📦 Installation

Le composant est déjà exporté depuis `@shared`. Il suffit de l'importer :

```typescript
import { EventActionButtonComponent } from '@shared';
```

## 🚀 Usage Basique

### Dans une liste d'événements

```typescript
// event-list.component.ts
import { EventActionButtonComponent } from '@shared';

@Component({
  imports: [EventActionButtonComponent],
  template: `
    <div *ngFor="let event of events()">
      <h3>{{ event.title }}</h3>

      <app-event-action-button
        [event]="event"
        [userId]="currentUserId()"
        [isOrganizer]="event.organizer_id === currentUserId()"
        [showBadge]="true"
        (actionTriggered)="handleAction($event, event)"
      />
    </div>
  `
})
export class EventListComponent {
  currentUserId = signal<number | null>(null);
  events = signal<EventDto[]>([]);

  handleAction(action: EventAction, event: EventDto) {
    switch (action) {
      case 'user-book':
        this.bookEvent(event);
        break;
      case 'user-pay-booking':
        this.payBooking(event);
        break;
      case 'organizer-start-game':
        this.startGame(event);
        break;
      // ... autres actions
    }
  }
}
```

### Dans une page de détail

```typescript
// event-detail.component.ts
@Component({
  imports: [EventActionButtonComponent],
  template: `
    <app-event-action-button
      [event]="event()"
      [userId]="currentUserId()"
      [isOrganizer]="isOrganizer()"
      [showBadge]="true"
      [size]="'lg'"
      [loading]="isProcessing()"
      (actionTriggered)="handleAction($event)"
      (viewDetails)="goToDetails($event)"
    />
  `
})
export class EventDetailComponent {
  event = signal<EventDetailDto | null>(null);
  currentUserId = signal<number | null>(null);
  isOrganizer = signal(false);
  isProcessing = signal(false);

  handleAction(action: EventAction) {
    this.isProcessing.set(true);
    // Traiter l'action
  }
}
```

## 📋 API

### Inputs

| Propriété | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `event` | `EventDto \| EventDetailDto` | ✅ Oui | - | L'événement pour lequel afficher les actions |
| `userId` | `number \| null` | ❌ Non | `null` | ID de l'utilisateur actuel (null si non connecté) |
| `isOrganizer` | `boolean` | ❌ Non | `false` | L'utilisateur est-il l'organisateur de cet événement ? |
| `isAdmin` | `boolean` | ❌ Non | `false` | L'utilisateur est-il admin ? |
| `showBadge` | `boolean` | ❌ Non | `true` | Afficher le badge d'état ? |
| `primaryOnly` | `boolean` | ❌ Non | `true` | Afficher uniquement le bouton primaire (sinon tous les boutons) |
| `size` | `'sm' \| 'md' \| 'lg'` | ❌ Non | `'md'` | Taille du bouton |
| `loading` | `boolean` | ❌ Non | `false` | État de chargement externe (désactive le bouton) |
| `forceAction` | `EventAction` | ❌ Non | - | Forcer une action spécifique (ignore la logique auto) |
| `hideViewDetails` | `boolean` | ❌ Non | `false` | Masquer le bouton "Voir les détails" (utile sur la page de détail) |

### Outputs

| Événement | Type | Description |
|-----------|------|-------------|
| `actionTriggered` | `EventAction` | Émis quand une action est déclenchée par l'utilisateur |
| `viewDetails` | `number` | Émis quand "Voir les détails" est cliqué (event ID) |

## 🎭 Types d'Actions Disponibles

### Organisateur - DRAFT
- `organizer-pay-and-publish` : Payer et publier l'événement (7€)
- `organizer-delete-draft` : Supprimer le brouillon

### Organisateur - PUBLISHED
- `organizer-start-game` : Lancer le jeu (si jeu configuré + événement commencé)
- `organizer-join-game` : Rejoindre le jeu en cours
- `organizer-cancel-event` : Annuler l'événement (si > 3h avant début)

### Utilisateur - PUBLISHED
- `user-book` : Réserver une place (si pas encore réservé + places disponibles)
- `user-pay-booking` : Payer une réservation PENDING
- `user-cancel-booking` : Annuler une réservation CONFIRMED (si > 3h avant)
- `user-join-game` : Rejoindre le jeu en cours (si réservation CONFIRMED + jeu démarré)

### Informations
- `view-details` : Voir les détails de l'événement

## 🏷️ Badges Automatiques

Le composant affiche automatiquement des badges selon l'état :

| Badge | Condition | Variante |
|-------|-----------|----------|
| `draft` | status === DRAFT | muted |
| `pending-confirmation` | status === PENDING_CONFIRMATION | muted |
| `published` | status === PUBLISHED | success |
| `full` | Événement complet | danger |
| `cancelled` | status === CANCELLED | danger |
| `finished` | status === FINISHED | muted |
| `starting-soon` | Démarre dans < 1h | accent |
| `game-live` | Jeu en cours | success |

## 🚫 Raisons de Désactivation

Quand un bouton est désactivé, un tooltip explicatif s'affiche automatiquement :

| Raison | Message (FR) |
|--------|--------------|
| `event-full` | L'événement est complet. Toutes les places sont réservées. |
| `event-cancelled` | Cet événement a été annulé par l'organisateur. |
| `event-finished` | Cet événement est terminé. |
| `booking-pending` | Vous avez déjà une réservation en attente de paiement. |
| `booking-confirmed` | Votre réservation est confirmée. |
| `cancellation-deadline-passed` | Le délai d'annulation est dépassé (moins de 3h avant). |
| `game-not-started` | Le jeu n'a pas encore été lancé par l'organisateur. |
| `no-confirmed-booking` | Vous devez avoir une réservation confirmée pour rejoindre le jeu. |

## 🎨 Exemples d'Usage Avancés

### Mode multi-boutons

Afficher tous les boutons disponibles (utile pour page de détail) :

```html
<app-event-action-button
  [event]="event()"
  [userId]="currentUserId()"
  [isOrganizer]="isOrganizer()"
  [primaryOnly]="false"
  (actionTriggered)="handleAction($event)"
/>
```

### Forcer une action spécifique

Utile quand vous voulez afficher un bouton précis sans la logique automatique :

```html
<app-event-action-button
  [event]="event()"
  [userId]="currentUserId()"
  [forceAction]="'user-cancel-booking'"
  (actionTriggered)="cancelBooking()"
/>
```

### Avec état de chargement

Désactiver le bouton pendant un traitement :

```html
<app-event-action-button
  [event]="event()"
  [userId]="currentUserId()"
  [isOrganizer]="isOrganizer()"
  [loading]="paymentProcessing()"
  (actionTriggered)="handlePayment($event)"
/>
```

## 🔧 Service Sous-jacent

Le composant utilise `EventActionsService` qui contient toute la logique métier.

### Utiliser le service directement

Si vous voulez juste la logique sans le composant :

```typescript
import { EventActionsService } from '@app/features/events/services/event-actions.service';

constructor(private actionsService: EventActionsService) {}

checkActions() {
  const actions = this.actionsService.getAvailableActions(event, {
    userId: this.currentUserId(),
    isOrganizer: true
  });

  const primaryAction = this.actionsService.getPrimaryAction(event, userContext);
  const badge = this.actionsService.getEventBadge(event);
  const isFull = this.actionsService.isEventFull(event);
  const canCancel = this.actionsService.canCancelBooking(event);
}
```

## 🌍 Traductions

Toutes les traductions sont disponibles en **Français**, **Anglais** et **Néerlandais** :

- **Labels des actions** : `events.actions.*`
- **Badges d'état** : `events.badges.*`
- **Raisons de désactivation** : `events.disabled_reasons.*`

Exemple :
```json
{
  "events": {
    "actions": {
      "book": "Réserver ma place",
      "pay_booking": "Payer ma réservation"
    },
    "badges": {
      "full": "Complet",
      "game-live": "🎮 Jeu en direct"
    },
    "disabled_reasons": {
      "event-full": "L'événement est complet. Toutes les places sont réservées."
    }
  }
}
```

## ✅ Bonnes Pratiques

1. **Toujours passer `userId`** : Permet au composant de déterminer correctement les actions disponibles
2. **Utiliser `loading`** : Améliore l'UX pendant les traitements asynchrones
3. **Gérer tous les types d'actions** : Utilisez un `switch` dans `handleAction()` pour couvrir tous les cas
4. **Laisser la logique au service** : Ne dupliquez pas la logique dans vos composants
5. **Utiliser `primaryOnly=false`** sur les pages de détail pour plus de visibilité

## 🐛 Dépannage

### Le bouton n'apparaît pas
- Vérifiez que `event` est bien défini et non null
- Vérifiez que le composant est importé dans votre module/composant

### Le bouton est toujours désactivé
- Vérifiez `userId` et `isOrganizer`
- Consultez les permissions backend dans `event.permissions`
- Vérifiez l'état de `loading`

### Les traductions ne fonctionnent pas
- Vérifiez que le `TPipe` est bien importé
- Vérifiez que les clés existent dans fr.json, en.json, nl.json

## 📝 License

MIT © Conversa
