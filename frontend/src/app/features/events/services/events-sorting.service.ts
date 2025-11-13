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
  | 'bidirectional'
  | 'target_language'
  | 'support'
  | 'almost_full'
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
   */
  sortEvents(events: EventDto[], criteria: SortingCriteria): ScoredEvent[] {
    const scored = events.map(event => this.scoreEvent(event, criteria));
    return scored.sort((a, b) => b.score - a.score);
  }

  /**
   * Calcule le score d'un événement basé sur les critères utilisateur
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
    const userSpeaksEventLang = userNative.includes(eventLang);
    const userLearningEventLang = userTargets.includes(eventLang);
    const canSupport =
      userSpeaksEventLang &&
      ((userNative.filter((l) => l !== eventLang).length > 0) ||
        userTargets.filter((l) => l !== eventLang).length > 0);
    const bidirectional = userSpeaksEventLang && userLearningEventLang;

    if (criteria.userCity && this.isNearby(event, criteria.userCity)) {
      score += 40;
      isNearby = true;
      reasons.push('events.sort_reason.nearby');
    }

    if (bidirectional) {
      score += 200;
      isRecommended = true;
      badge = 'bidirectional';
      reasons.push('events.sort_reason.bidirectional');
    } else if (userLearningEventLang) {
      score += 130;
      isRecommended = true;
      if (!badge) badge = 'target_language';
      reasons.push('events.sort_reason.target_language');
    } else if (userSpeaksEventLang) {
      score += 90;
      reasons.push('events.sort_reason.native_language');
    }

    if (canSupport) {
      score += 60;
      if (!badge) badge = 'support';
      reasons.push('events.sort_reason.support');
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
      score += 70;
      if (!badge) badge = 'almost_full';
      reasons.push('events.sort_reason.almost_full');
    }

    if (event.alreadyBooked) {
      score -= 300;
      reasons.push('events.sort_reason.already_booked');
    }

    if (event.is_full) {
      score -= 1200;
      badge = 'full';
    }
    if (event.is_cancelled) {
      score -= 1300;
      badge = 'cancelled';
    }
    if (this.isPast(event)) {
      score -= 1500;
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
