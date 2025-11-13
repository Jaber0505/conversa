import { Injectable } from '@angular/core';
import { EventDto } from '@core/models';

export interface SortingCriteria {
  userCity?: string;
  userTargetLangs?: string[];
  userNativeLangs?: string[];
}

export interface ScoredEvent {
  event: EventDto;
  score: number;
  isRecommended: boolean;
  isNearby: boolean;
  reasons: string[];
  badgeReason: PriorityBadge | null;
}

export type PriorityBadge =
  | 'recommended'
  | 'full'
  | 'cancelled';

/**
 * Service intelligent de tri des événements
 * Priorise les événements selon plusieurs critères :
 * - Localisation (ville de l'utilisateur)
 * - Langues cibles de l'utilisateur
 * - Langues natives (pour pratiquer)
 */
@Injectable({ providedIn: 'root' })
export class EventsSortingService {
  /**
   * Trie les événements selon les critères de l'utilisateur
   * Limite les événements recommandés à un maximum de 5
   */
  sortEvents(events: EventDto[], criteria: SortingCriteria): ScoredEvent[] {
    const scored = events.map(event => this.scoreEvent(event, criteria));
    const sorted = scored.sort((a, b) => b.score - a.score);

    // Limiter les recommandations à 5 événements maximum
    let recommendedCount = 0;
    const maxRecommendations = 5;

    return sorted.map(scoredEvent => {
      // Si l'événement était recommandé mais qu'on a atteint la limite
      if (scoredEvent.isRecommended &&
          scoredEvent.badgeReason === 'recommended' &&
          recommendedCount >= maxRecommendations) {
        // Retirer le statut recommandé et le badge
        return {
          ...scoredEvent,
          isRecommended: false,
          badgeReason: null
        };
      }

      // Compter les événements recommandés
      if (scoredEvent.isRecommended && scoredEvent.badgeReason === 'recommended') {
        recommendedCount++;
      }

      return scoredEvent;
    });
  }

  /**
   * Calcule le score d'un événement basé sur les critères utilisateur
   *
   * Nouveau système de recommandation simplifié :
   * - +++ (300 pts) : Bidirectionnel - l'utilisateur parle la langue de l'événement ET les participants parlent la langue cible de l'utilisateur
   * - ++ (200 pts) : L'utilisateur parle la langue de l'événement (peut participer activement)
   * - + (100 pts) : L'utilisateur peut apporter une aide à l'événement
   */
  private scoreEvent(event: EventDto, criteria: SortingCriteria): ScoredEvent {
    let score = 0;
    const reasons: string[] = [];
    let isRecommended = false;
    let isNearby = false;
    let badge: PriorityBadge | null = null;

    const userNative = (criteria.userNativeLangs ?? []).map((l) => l.toLowerCase());
    const userTargets = (criteria.userTargetLangs ?? []).map((l) => l.toLowerCase());
    const eventLang = (event.language_code || '').toLowerCase();

    // L'utilisateur parle la langue de l'événement
    const userSpeaksEventLang = userNative.includes(eventLang);

    // L'utilisateur apprend la langue de l'événement
    const userLearningEventLang = userTargets.includes(eventLang);

    // Bidirectionnel : l'utilisateur parle la langue de l'événement ET apprend cette langue aussi
    // (implique un échange mutuel possible)
    const bidirectional = userSpeaksEventLang && userLearningEventLang;

    // L'utilisateur peut apporter une aide (parle la langue de l'événement et peut aider avec d'autres langues)
    const canSupport =
      userSpeaksEventLang &&
      ((userNative.filter((l) => l !== eventLang).length > 0) ||
        userTargets.filter((l) => l !== eventLang).length > 0);

    // === SCORING PRINCIPAL (langue uniquement) ===

    if (bidirectional) {
      // +++ : Échange bidirectionnel possible
      score += 300;
      isRecommended = true;
      badge = 'recommended';
      reasons.push('events.sort_reason.bidirectional');
    } else if (userSpeaksEventLang) {
      // ++ : Peut participer activement à l'événement
      score += 200;
      isRecommended = true;
      badge = 'recommended';
      reasons.push('events.sort_reason.native_language');
    } else if (canSupport) {
      // + : Peut apporter une aide à l'événement
      score += 100;
      isRecommended = true;
      badge = 'recommended';
      reasons.push('events.sort_reason.support');
    }

    // === BONUS DE TRI (ne changent pas le statut "recommandé") ===

    if (criteria.userCity && this.isNearby(event, criteria.userCity)) {
      score += 40;
      isNearby = true;
      reasons.push('events.sort_reason.nearby');
    }

    if (event.price_cents === 0) {
      score += 20;
      reasons.push('events.sort_reason.free');
    }

    if (this.isComingSoon(event)) {
      score += 10;
      reasons.push('events.sort_reason.coming_soon');
    }

    const occupancy = this.getOccupancyRatio(event);
    const isAlmostFull = occupancy >= 0.8 && occupancy < 1 && !event.is_full;
    if (isAlmostFull) {
      score += 5;
      reasons.push('events.sort_reason.almost_full');
    }

    // === PÉNALITÉS (garde la même logique) ===

    if (event.alreadyBooked) {
      score -= 300;
      reasons.push('events.sort_reason.already_booked');
    }

    if (event.is_full) {
      score -= 1200;
      badge = 'full';
      isRecommended = false;
    }
    if (event.is_cancelled) {
      score -= 1300;
      badge = 'cancelled';
      isRecommended = false;
    }
    if (this.isPast(event)) {
      score -= 1500;
      isRecommended = false;
    }

    return {
      event,
      score,
      isRecommended,
      isNearby,
      reasons,
      badgeReason: badge,
    };
  }


  /**
   * Vérifie si un événement est proche de la ville de l'utilisateur
   */
  private isNearby(event: EventDto, userCity: string): boolean {
    const city = userCity.toLowerCase().trim();
    const eventCity = (event.partner_city || event.address || '').toLowerCase();
    return eventCity.includes(city);
  }

  /**
   * Vérifie si un événement arrive bientôt (dans les 7 prochains jours)
   */
  private isComingSoon(event: EventDto): boolean {
    if (!event.datetime_start) return false;

    const now = new Date();
    const eventDate = new Date(event.datetime_start);
    const diffInDays = (eventDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24);

    return diffInDays > 0 && diffInDays <= 7;
  }

  /**
   * Filtre les événements selon une recherche textuelle (insensible à la casse et aux accents)
   */
  filterBySearch(events: ScoredEvent[], searchQuery: string): ScoredEvent[] {
    if (!searchQuery || searchQuery.trim() === '') {
      return events;
    }

    const normalizedQuery = this.normalizeString(searchQuery);

    return events.filter(({ event }) => {
      const searchableFields = [
        event.title,
        event.theme,
        event.address,
        event.partner_city,
        event.language_code,
        event.partner_address
      ].filter(Boolean);

      return searchableFields.some(field =>
        this.normalizeString(field!).includes(normalizedQuery)
      );
    });
  }

  /**
   * Normalise une chaîne pour la recherche (minuscules, sans accents)
   */
  private normalizeString(str: string): string {
    return str
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '');
  }

  private getOccupancyRatio(event: EventDto): number {
    const max = event.max_participants || 0;
    if (!max) return 0;
    const booked =
      (event as any).booked_seats ??
      event.registration_count ??
      0;
    return Math.min(1, booked / max);
  }

  private isPast(event: EventDto): boolean {
    if (!event.datetime_start) return false;
    return new Date(event.datetime_start).getTime() < Date.now();
  }
}
