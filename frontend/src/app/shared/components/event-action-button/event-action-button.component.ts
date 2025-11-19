import { Component, Input, Output, EventEmitter, inject, computed, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TPipe } from '@core/i18n';
import { EventDto, EventDetailDto } from '@core/models';
import { ButtonComponent, BadgeComponent } from '@shared';
import {
  EventActionsService,
  EventActionState,
  EventAction,
  UserContext,
  ButtonVariant
} from '@app/features/events/services/event-actions.service';

/**
 * Composant réutilisable pour afficher les boutons d'action d'un événement.
 *
 * Gère automatiquement :
 * - L'affichage du bouton principal selon le contexte
 * - L'activation/désactivation selon les règles métier
 * - Les badges d'état
 * - Les tooltips explicatifs
 * - L'émission des événements d'action
 *
 * Usage :
 * ```html
 * <app-event-action-button
 *   [event]="event"
 *   [userId]="currentUserId"
 *   [isOrganizer]="isOrganizer"
 *   [showBadge]="true"
 *   [size]="'md'"
 *   (actionTriggered)="handleAction($event)"
 * />
 * ```
 */
@Component({
  selector: 'app-event-action-button',
  standalone: true,
  imports: [CommonModule, TPipe, ButtonComponent, BadgeComponent],
  templateUrl: './event-action-button.component.html',
  styleUrls: ['./event-action-button.component.scss']
})
export class EventActionButtonComponent {
  private readonly actionsService = inject(EventActionsService);

  // ==================== INPUTS ====================

  /** L'événement pour lequel afficher l'action */
  @Input({ required: true }) event!: EventDto | EventDetailDto;

  /** ID de l'utilisateur actuel (null si non connecté) */
  @Input() userId: number | null = null;

  /** L'utilisateur est-il l'organisateur ? */
  @Input() isOrganizer = false;

  /** L'utilisateur est-il admin ? */
  @Input() isAdmin = false;

  /** Afficher le badge d'état ? */
  @Input() showBadge = true;

  /** Afficher uniquement le bouton primaire ? (sinon affiche tous les boutons) */
  @Input() primaryOnly = true;

  /** Taille du bouton */
  @Input() size: 'sm' | 'md' | 'lg' = 'md';

  /** État de chargement externe (ex: paiement en cours) */
  @Input() loading = false;

  /** Forcer une action spécifique (ignore la logique automatique) */
  @Input() forceAction?: EventAction;

  /** Masquer le bouton "Voir les détails" (utile quand on est déjà sur la page de détail) */
  @Input() hideViewDetails = false;

  /** Mode test activé (ignore la validation d'heure pour afficher le bouton jeu) */
  private _skipTimeValidation = signal(false);
  @Input()
  set skipTimeValidation(value: boolean) {
    this._skipTimeValidation.set(value);
  }
  get skipTimeValidation(): boolean {
    return this._skipTimeValidation();
  }

  // ==================== OUTPUTS ====================

  /** Émis quand une action est déclenchée */
  @Output() actionTriggered = new EventEmitter<EventAction>();

  /** Émis quand le bouton "Voir détails" est cliqué */
  @Output() viewDetails = new EventEmitter<number>();

  // ==================== INTERNAL STATE ====================

  /** État de chargement interne (géré par le composant) */
  private internalLoading = signal(false);

  /** Action actuellement en cours d'exécution */
  private currentAction = signal<EventAction | null>(null);

  // ==================== COMPUTED SIGNALS ====================

  /** Contexte utilisateur */
  private userContext = computed<UserContext>(() => ({
    userId: this.userId,
    isOrganizer: this.isOrganizer,
    isAdmin: this.isAdmin,
    skipTimeValidation: this._skipTimeValidation()
  }));

  /** Action principale à afficher */
  primaryAction = computed<EventActionState | null>(() => {
    if (this.forceAction) {
      const actions = this.actionsService.getAvailableActions(this.event, this.userContext());
      return actions.find(a => a.action === this.forceAction) || null;
    }
    return this.actionsService.getPrimaryAction(this.event, this.userContext());
  });

  /** Toutes les actions disponibles (mode multi-boutons) */
  allActions = computed<EventActionState[]>(() => {
    const actions = this.actionsService.getAvailableActions(this.event, this.userContext());
    // Filtrer "view-details" si hideViewDetails est activé
    if (this.hideViewDetails) {
      return actions.filter(action => action.action !== 'view-details');
    }
    return actions;
  });

  /** Badge d'état de l'événement */
  eventBadge = computed(() => this.actionsService.getEventBadge(this.event));

  /** Clé de traduction du badge */
  badgeLabelKey = computed(() => {
    const badge = this.eventBadge();
    if (!badge) return null;
    return `events.badges.${badge}`;
  });

  /** Variante du badge */
  badgeVariant = computed<'primary' | 'accent' | 'success' | 'danger' | 'muted'>(() => {
    const badge = this.eventBadge();
    switch (badge) {
      case 'cancelled':
      case 'full':
        return 'danger';
      case 'game-live':
      case 'published':
        return 'success';
      case 'starting-soon':
        return 'accent';
      case 'pending-confirmation':
      case 'draft':
        return 'muted';
      default:
        return 'primary';
    }
  });

  /** État de chargement global (externe + interne) */
  isLoading = computed(() => this.loading || this.internalLoading());

  /** Vérifie si une action spécifique est en cours */
  isActionLoading = (action: EventAction) =>
    this.internalLoading() && this.currentAction() === action;

  // ==================== METHODS ====================

  /**
   * Gérer le clic sur un bouton d'action.
   */
  onActionClick(action: EventAction, event?: Event): void {
    // Empêcher la propagation vers le parent (la carte cliquable)
    if (event) {
      event.stopPropagation();
      event.preventDefault();
    }

    if (this.isLoading()) return;

    // Actions spéciales gérées en interne
    if (action === 'view-details') {
      this.viewDetails.emit(this.event.id);
      return;
    }

    // Activer le loading interne
    this.internalLoading.set(true);
    this.currentAction.set(action);

    // Émettre l'événement pour que le parent gère l'action
    this.actionTriggered.emit(action);

    // Désactiver le loading après 2 secondes (sécurité)
    // Le parent devrait gérer son propre loading, mais en cas d'oubli
    setTimeout(() => {
      this.internalLoading.set(false);
      this.currentAction.set(null);
    }, 2000);
  }

  /**
   * Obtenir la variante du bouton selon le variant de l'action.
   * Map les variantes du service vers celles acceptées par ButtonComponent.
   */
  getButtonVariant(variant: ButtonVariant): 'primary' | 'accent' | 'danger' | 'outline' | 'link' {
    return variant;
  }

  /**
   * Obtenir le tooltip d'une action désactivée.
   */
  getDisabledTooltip(action: EventActionState): string {
    if (!action.disabledReason) return '';
    return `events.disabled_reasons.${action.disabledReason}`;
  }
}
