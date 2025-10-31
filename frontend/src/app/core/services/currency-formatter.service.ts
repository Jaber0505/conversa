import { Injectable } from '@angular/core';

/**
 * Service de formatage monétaire
 * Centralise la logique de formatage des montants en EUR
 */
@Injectable({ providedIn: 'root' })
export class CurrencyFormatterService {
  /**
   * Formate un montant en centimes en devise EUR
   * @param cents Montant en centimes (ex: 1500 = 15.00 EUR)
   * @param locale Locale à utiliser (défaut: 'fr-BE')
   * @returns Format monétaire (ex: "15,00 €")
   */
  formatEUR(cents: number, locale: string = 'fr-BE'): string {
    const amount = (cents ?? 0) / 100;
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: 'EUR'
    }).format(amount);
  }

  /**
   * Formate un montant multiplié par un multiplicateur (ex: nombre de places)
   * @param cents Montant unitaire en centimes
   * @param multiplier Multiplicateur (ex: nombre de sièges)
   * @param locale Locale à utiliser
   * @returns Format monétaire ou 'Gratuit' si montant = 0, ou null si cents undefined
   */
  formatEURWithMultiplier(
    cents: number | undefined,
    multiplier: number = 1,
    locale: string = 'fr-BE'
  ): string | null {
    if (cents == null) return null;
    const total = cents * multiplier;
    if (total === 0) return 'Gratuit';
    return this.formatEUR(total, locale);
  }
}
