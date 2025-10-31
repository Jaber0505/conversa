import { Pipe, PipeTransform, inject } from '@angular/core';
import { CurrencyFormatterService } from '@app/core/services/currency-formatter.service';

/**
 * Pipe pour formater les montants en centimes en EUR
 * Usage: {{ amount_cents | currency }}
 * Usage avec multiplicateur: {{ price_cents | currency:seat_count }}
 */
@Pipe({
  name: 'currency',
  standalone: true
})
export class CurrencyPipe implements PipeTransform {
  private formatter = inject(CurrencyFormatterService);

  transform(cents: number | undefined, multiplier: number = 1): string {
    return this.formatter.formatEURWithMultiplier(cents, multiplier) ?? '—';
  }
}
