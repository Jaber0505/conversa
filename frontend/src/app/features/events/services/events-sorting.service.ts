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
}

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
   * Trie les événements de manière intelligente selon les critères utilisateur
   * Score: Plus le score est élevé, plus l'événement est recommandé
   */
  sortEvents(events: EventDto[], criteria: SortingCriteria): ScoredEvent[] {
    return events
      .map(event => this.scoreEvent(event, criteria))
      .sort((a, b) => b.score - a.score);
  }

  /**
   * Calcule le score d'un événement basé sur les critères utilisateur
   */
  private scoreEvent(event: EventDto, criteria: SortingCriteria): ScoredEvent {
    let score = 0;
    const reasons: string[] = [];
    let isRecommended = false;
    let isNearby = false;

    // Critère 1: Localisation (+50 points)
    if (criteria.userCity && this.isNearby(event, criteria.userCity)) {
      score += 50;
      isNearby = true;
      reasons.push('events.sort_reason.nearby');
    }

    // Critère 2: Langue cible de l'utilisateur (+100 points - TRÈS IMPORTANT)
    if (criteria.userTargetLangs && criteria.userTargetLangs.length > 0) {
      if (criteria.userTargetLangs.includes(event.language_code)) {
        score += 100;
        isRecommended = true;
        reasons.push('events.sort_reason.target_language');
      }
    }

    // Critère 3: Langue native (pour pratiquer, +30 points)
    if (criteria.userNativeLangs && criteria.userNativeLangs.length > 0) {
      if (criteria.userNativeLangs.includes(event.language_code)) {
        score += 30;
        reasons.push('events.sort_reason.native_language');
      }
    }

    // Critère 4: Événement gratuit (+20 points)
    if (event.price_cents === 0) {
      score += 20;
      reasons.push('events.sort_reason.free');
    }

    // Critère 5: Événement à venir bientôt (+10 points)
    if (this.isComingSoon(event)) {
      score += 10;
      reasons.push('events.sort_reason.coming_soon');
    }

    // Malus: Événement déjà réservé (-500 points) - doit apparaître en dernier
    if (event.alreadyBooked) {
      score -= 500;
      reasons.push('events.sort_reason.already_booked');
    }

    // Malus: Événement annulé (-1000 points)
    if (event.is_cancelled) {
      score -= 1000;
    }

    return {
      event,
      score,
      isRecommended,
      isNearby,
      reasons
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
        event.language_code
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
}
