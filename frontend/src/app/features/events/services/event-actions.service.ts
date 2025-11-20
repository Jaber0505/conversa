import { Injectable } from '@angular/core';
import { EventDto, EventDetailDto } from '@core/models';

/**
 * État d'une action disponible pour un événement.
 */
export interface EventActionState {
  /** Type d'action disponible */
  action: EventAction;
  /** L'action est-elle disponible ? */
  enabled: boolean;
  /** Raison de désactivation (si enabled = false) */
  disabledReason?: DisabledReason;
  /** Badge à afficher (optionnel) */
  badge?: EventBadge;
  /** Variante du bouton (visual style) */
  variant: ButtonVariant;
  /** Label de traduction du bouton */
  labelKey: string;
  /** Icône à afficher (optionnel) */
  icon?: string;
  /** Action est-elle visible ? */
  visible: boolean;
  /** Priorité d'affichage (0 = plus haute) */
  priority: number;
}

/**
 * Types d'actions possibles sur un événement.
 */
export type EventAction =
  // Organisateur - DRAFT
  | 'organizer-pay-and-publish'
  | 'organizer-delete-draft'
  // Organisateur - PUBLISHED
  | 'organizer-cancel-event'
  | 'organizer-start-game'
  | 'organizer-join-game'
  // Utilisateur - PUBLISHED
  | 'user-book'
  | 'user-pay-booking'
  | 'user-cancel-booking'
  | 'user-join-game'
  // Informations
  | 'view-details';

/**
 * Raisons de désactivation d'une action.
 */
export type DisabledReason =
  | 'event-full'
  | 'event-cancelled'
  | 'event-finished'
  | 'booking-pending'
  | 'booking-confirmed'
  | 'already-booked'
  | 'cancellation-deadline-passed'
  | 'booking-cutoff-passed'
  | 'event-not-started'
  | 'game-not-configured'
  | 'game-not-started'
  | 'no-confirmed-booking'
  | 'insufficient-permissions';

/**
 * Badges d'état d'événement.
 */
export type EventBadge =
  | 'draft'
  | 'pending-confirmation'
  | 'published'
  | 'full'
  | 'cancelled'
  | 'finished'
  | 'starting-soon'
  | 'game-live';

/**
 * Variantes visuelles des boutons.
 */
export type ButtonVariant = 'primary' | 'accent' | 'danger' | 'outline' | 'link';

/**
 * Contexte utilisateur pour déterminer les actions disponibles.
 */
export interface UserContext {
  /** ID de l'utilisateur actuel */
  userId: number | null;
  /** L'utilisateur est-il l'organisateur de cet événement ? */
  isOrganizer: boolean;
  /** L'utilisateur est-il admin ? */
  isAdmin?: boolean;
  /** Mode test activé (pour organisateur uniquement) */
  skipTimeValidation?: boolean;
}

/**
 * Service centralisé pour la logique métier des actions d'événements.
 *
 * Détermine quelles actions sont disponibles selon :
 * - Le statut de l'événement (DRAFT, PUBLISHED, CANCELLED, etc.)
 * - Le rôle de l'utilisateur (organisateur, participant, visiteur)
 * - Le contexte (réservation existante, capacité, délais)
 * - Les permissions backend (_links, permissions)
 */
@Injectable({
  providedIn: 'root'
})
export class EventActionsService {
  private readonly CANCELLATION_DEADLINE_HOURS = 3;
  private readonly BOOKING_CUTOFF_MINUTES = 15;

  /**
   * Détermine toutes les actions disponibles pour un événement donné.
   *
   * @param event L'événement à analyser
   * @param userContext Le contexte de l'utilisateur actuel
   * @returns Liste des actions disponibles, triées par priorité
   */
  getAvailableActions(
    event: EventDto | EventDetailDto,
    userContext: UserContext
  ): EventActionState[] {
    const actions: EventActionState[] = [];

    // Déterminer l'action principale selon le contexte
    if (userContext.isOrganizer) {
      actions.push(...this.getOrganizerActions(event, userContext));
    } else {
      actions.push(...this.getUserActions(event as EventDetailDto, userContext));
    }

    // Ajouter une action "voir les détails" si aucune n'est présente
    const hasViewDetails = actions.some(
      (a) => a.action === 'view-details' && a.labelKey === 'events.actions.view_details'
    );
    if (!hasViewDetails) {
      actions.push({
        action: 'view-details',
        enabled: true,
        visible: true,
        variant: 'outline',
        labelKey: 'events.actions.view_details',
        priority: 100
      });
    }

    // Trier par priorité
    return actions.sort((a, b) => a.priority - b.priority);
  }

  /**
   * Obtenir l'action principale à afficher (la plus prioritaire et enabled).
   */
  getPrimaryAction(
    event: EventDto | EventDetailDto,
    userContext: UserContext
  ): EventActionState | null {
    const actions = this.getAvailableActions(event, userContext);
    return actions.find(a => a.enabled && a.visible) || null;
  }

  /**
   * Obtenir le badge d'état à afficher pour un événement.
   */
  getEventBadge(event: EventDto | EventDetailDto): EventBadge | null {
    // Priorité : cancelled > finished > full > starting-soon > game-live > published > pending > draft
    if (event.status === 'CANCELLED') return 'cancelled';
    if (event.status === 'FINISHED') return 'finished';
    if (this.isEventFull(event)) return 'full';

    // Game live
    if (event.game_started) return 'game-live';

    // Starting soon (< 1h)
    const now = new Date();
    const start = new Date(event.datetime_start);
    const hoursUntilStart = (start.getTime() - now.getTime()) / (1000 * 60 * 60);
    if (hoursUntilStart > 0 && hoursUntilStart < 1 && event.status === 'PUBLISHED') {
      return 'starting-soon';
    }

    if (event.status === 'PUBLISHED') return 'published';
    if (event.status === 'PENDING_CONFIRMATION') return 'pending-confirmation';
    if (event.status === 'DRAFT') return 'draft';

    return null;
  }

  /**
   * Vérifier si l'événement est complet.
   */
  isEventFull(event: EventDto | EventDetailDto): boolean {
    if (typeof event.is_full === 'boolean') {
      return event.is_full;
    }
    const max = event.max_participants || 0;
    if (!max) return false;
    const current = event.booked_seats ?? event.registration_count ?? 0;
    return current >= max;
  }

  /**
   * Vérifier si l'événement a commencé.
   */
  hasEventStarted(event: EventDto | EventDetailDto): boolean {
    const now = new Date();
    const start = new Date(event.datetime_start);
    return now >= start;
  }

  /**
   * Vérifier si on peut annuler (deadline de 3h).
   */
  canCancelBooking(event: EventDto | EventDetailDto): boolean {
    const now = new Date();
    const start = new Date(event.datetime_start);
    const hoursUntilStart = (start.getTime() - now.getTime()) / (1000 * 60 * 60);
    return hoursUntilStart >= this.CANCELLATION_DEADLINE_HOURS;
  }

  /**
   * Vérifier si on peut encore réserver (cutoff de 15 minutes).
   */
  canBookEvent(event: EventDto | EventDetailDto): boolean {
    const now = new Date();
    const start = new Date(event.datetime_start);
    const minutesUntilStart = (start.getTime() - now.getTime()) / (1000 * 60);
    return minutesUntilStart >= this.BOOKING_CUTOFF_MINUTES;
  }

  // ==================== ACTIONS ORGANISATEUR ====================

  private getOrganizerActions(
    event: EventDto | EventDetailDto,
    userContext: UserContext
  ): EventActionState[] {
    const actions: EventActionState[] = [];
    const links = (event as any)._links || {};
    const perms = (event as any).permissions || {};

    // Si l'événement est annulé, aucune action n'est possible
    if (event.status === 'CANCELLED' || event.is_cancelled) {
      actions.push({
        action: 'view-details',
        enabled: true,
        visible: true,
        variant: 'outline',
        labelKey: 'events.actions.view_details',
        priority: 0
      });
      return actions;
    }

    if (event.status === 'DRAFT') {
      // Action : Payer et publier
      if (links.request_publication || links.pay_and_publish) {
        actions.push({
          action: 'organizer-pay-and-publish',
          enabled: true,
          visible: true,
          variant: 'primary',
          labelKey: 'events.actions.pay_and_publish',
          priority: 0
        });
      }

      // Action : Supprimer le brouillon
      if (links.delete_draft) {
        actions.push({
          action: 'organizer-delete-draft',
          enabled: true,
          visible: true,
          variant: 'danger',
          labelKey: 'events.actions.delete_draft',
          priority: 1
        });
      }
    }

    if (event.status === 'PENDING_CONFIRMATION') {
      // Pas d'action, juste un badge
      actions.push({
        action: 'view-details',
        enabled: false,
        visible: true,
        variant: 'outline',
        labelKey: 'events.actions.pending_confirmation',
        disabledReason: 'insufficient-permissions',
        badge: 'pending-confirmation',
        priority: 0
      });
    }

    if (event.status === 'PUBLISHED') {
      const hasStarted = this.hasEventStarted(event);
      const hasGame = !!event.game_type;
      const canShowGame = hasStarted || (userContext.isOrganizer && userContext.skipTimeValidation);

      // Si le jeu est lancé, afficher UNIQUEMENT le bouton "Rejoindre le jeu"
      if (event.game_started && hasGame) {
        actions.push({
          action: 'organizer-join-game',
          enabled: true,
          visible: true,
          variant: 'accent',
          labelKey: 'events.actions.join_game',
          badge: 'game-live',
          priority: 0
        });
        // Ne pas afficher d'autres actions si le jeu est lancé
        return actions;
      }

      // Jeu pas encore lancé : afficher le bouton "Lancer le jeu"
      if (hasGame && canShowGame) {
        actions.push({
          action: 'organizer-start-game',
          enabled: true,
          visible: true,
          variant: 'accent',
          labelKey: 'events.actions.start_game',
          priority: 0
        });
      }

      // Action : Annuler l'événement (seulement si le jeu n'est pas lancé)
      if (perms.can_cancel_event || links.cancel) {
        const canCancel = this.canCancelBooking(event);
        actions.push({
          action: 'organizer-cancel-event',
          enabled: canCancel,
          visible: true,
          variant: 'danger',
          labelKey: 'events.actions.cancel_event',
          disabledReason: canCancel ? undefined : 'cancellation-deadline-passed',
          priority: hasStarted && hasGame ? 2 : 1
        });
      }
    }

    return actions;
  }

  // ==================== ACTIONS UTILISATEUR ====================

  private getUserActions(
    event: EventDetailDto,
    userContext: UserContext
  ): EventActionState[] {
    const actions: EventActionState[] = [];
    const links = (event as any)._links || {};
    const perms = event.permissions || {};
    const myBooking = event.my_booking;

    // Si la réservation est annulée, aucune action n'est possible (seulement voir les détails)
    if (myBooking?.status === 'CANCELLED') {
      actions.push({
        action: 'view-details',
        enabled: true,
        visible: true,
        variant: 'outline',
        labelKey: 'events.actions.view_details',
        priority: 0
      });
      return actions;
    }

    // Si l'événement est annulé, aucune action n'est possible
    if (event.status === 'CANCELLED' || event.is_cancelled) {
      actions.push({
        action: 'view-details',
        enabled: true,
        visible: true,
        variant: 'outline',
        labelKey: 'events.actions.view_details',
        priority: 0
      });
      return actions;
    }

    // Événements non accessibles pour utilisateurs normaux
    if (event.status === 'DRAFT' || event.status === 'PENDING_CONFIRMATION') {
      return [];
    }

    if (event.status === 'PUBLISHED') {
      const hasStarted = this.hasEventStarted(event);
      const hasGame = !!event.game_type;

      // Si le jeu est lancé et que l'utilisateur a une réservation CONFIRMED,
      // afficher UNIQUEMENT le bouton "Rejoindre le jeu"
      if (event.game_started && hasGame && myBooking?.status === 'CONFIRMED') {
        actions.push({
          action: 'user-join-game',
          enabled: true,
          visible: true,
          variant: 'accent',
          labelKey: 'events.actions.join_game',
          badge: 'game-live',
          priority: 0
        });
        // Ne pas afficher d'autres actions si le jeu est lancé
        return actions;
      }

      // Jeu configuré mais pas encore lancé : afficher bouton disabled
      if (hasStarted && hasGame && myBooking?.status === 'CONFIRMED' && !event.game_started) {
        actions.push({
          action: 'user-join-game',
          enabled: false,
          visible: true,
          variant: 'accent',
          labelKey: 'events.actions.join_game',
          disabledReason: 'game-not-started',
          priority: 0
        });
      }

      // Action : Payer une réservation PENDING
      if (myBooking?.status === 'PENDING') {
        actions.push({
          action: 'user-pay-booking',
          enabled: true,
          visible: true,
          variant: 'primary',
          labelKey: 'events.actions.pay_booking',
          badge: 'published',
          priority: 0
        });
      }

      // Action : Annuler une réservation CONFIRMED (seulement si jeu pas lancé)
      if (myBooking?.status === 'CONFIRMED' && !event.game_started) {
        const canCancel = this.canCancelBooking(event);
        actions.push({
          action: 'user-cancel-booking',
          enabled: canCancel,
          visible: true,
          variant: 'danger',
          labelKey: 'events.actions.cancel_booking',
          disabledReason: canCancel ? undefined : 'cancellation-deadline-passed',
          priority: hasStarted && hasGame ? 2 : 1
        });

        // Si pas d'action jeu, mais réservé : afficher badge
        if (!(hasStarted && hasGame)) {
          actions.push({
            action: 'view-details',
            enabled: false,
            visible: true,
            variant: 'outline',
            labelKey: canCancel ? 'events.actions.booking_confirmed' : 'events.actions.starting_soon',
            disabledReason: 'booking-confirmed',
            badge: canCancel ? 'published' : 'starting-soon',
            priority: 0
          });
        }
      }

      // Action : Réserver (si pas de réservation et événement pas plein)
      if (!myBooking) {
        const isFull = this.isEventFull(event);
        const isWithinCutoff = !this.canBookEvent(event);

        // Si permissions est défini, utiliser can_book, sinon fallback : utilisateur connecté + pas annulé + pas fini
        const hasPermission = perms.can_book !== undefined
          ? !!perms.can_book
          : (!!userContext.userId && event.status === 'PUBLISHED');
        const canBook = hasPermission && !isFull && !isWithinCutoff;

        // Déterminer le label et la raison
        let labelKey = 'events.actions.book';
        let disabledReason: DisabledReason | undefined = undefined;
        let badge: EventBadge | undefined = undefined;

        if (isWithinCutoff) {
          labelKey = 'events.actions.booking_closed';
          disabledReason = 'booking-cutoff-passed';
        } else if (isFull) {
          labelKey = 'events.actions.event_full';
          disabledReason = 'event-full';
          badge = 'full';
        }

        actions.push({
          action: 'user-book',
          enabled: canBook,
          visible: true,
          variant: 'primary',
          labelKey,
          disabledReason,
          badge,
          priority: 0
        });
      }
    }

    // Événement terminé
    if (event.status === 'FINISHED') {
      actions.push({
        action: 'view-details',
        enabled: false,
        visible: true,
        variant: 'outline',
        labelKey: 'events.actions.event_finished',
        disabledReason: 'event-finished',
        badge: 'finished',
        priority: 0
      });
    }

    return actions;
  }
}
