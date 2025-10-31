import { Injectable } from '@angular/core';

/**
 * Service de formatage de dates
 * Centralise la logique de formatage des dates ISO
 */
@Injectable({ providedIn: 'root' })
export class DateFormatterService {
  /**
   * Formate une date ISO en format lisible court avec heure
   * @param iso Date en format ISO (ex: "2024-10-30T19:00:00Z")
   * @param locale Locale à utiliser (défaut: 'fr-BE')
   * @returns Ex: "mer. 30 oct., 19:00" ou "—" si undefined
   */
  formatDateTime(iso: string | undefined, locale: string = 'fr-BE'): string {
    if (!iso) return '—';
    try {
      return new Intl.DateTimeFormat(locale, {
        weekday: 'short',
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
      }).format(new Date(iso));
    } catch {
      return iso;
    }
  }

  /**
   * Formate une date ISO en format court sans heure
   * @param iso Date en format ISO
   * @param locale Locale à utiliser (défaut: 'fr-BE')
   * @returns Ex: "30 oct. 2024"
   */
  formatDate(iso: string | undefined, locale: string = 'fr-BE'): string {
    if (!iso) return '—';
    try {
      return new Intl.DateTimeFormat(locale, {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      }).format(new Date(iso));
    } catch {
      return iso;
    }
  }
}
