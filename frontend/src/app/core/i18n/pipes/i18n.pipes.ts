import { Pipe, PipeTransform, inject } from '@angular/core';
import { formatDateIntl, formatNumberIntl, formatCurrencyIntl, Lang, LangService } from '@core/i18n';

/** Date localisée : {{ value | tDate:options[:langOverride] }} */
@Pipe({ name: 'tDate', standalone: true, pure: false })
export class TDatePipe implements PipeTransform {
  private readonly lang = inject(LangService);
  transform(value: Date | string | number, options?: Intl.DateTimeFormatOptions, langOverride?: Lang): string {
    const lang = langOverride ?? this.lang.current;
    return formatDateIntl(value, lang, options);
  }
}

/** Nombre localisé : {{ value | tNumber:options[:langOverride] }} */
@Pipe({ name: 'tNumber', standalone: true, pure: false })
export class TNumberPipe implements PipeTransform {
  private readonly lang = inject(LangService);
  transform(value: number, options?: Intl.NumberFormatOptions, langOverride?: Lang): string {
    const lang = langOverride ?? this.lang.current;
    return formatNumberIntl(value, lang, options);
  }
}

/** Devise localisée : {{ value | tCurrency:currency[:options][:langOverride] }} */
@Pipe({ name: 'tCurrency', standalone: true, pure: false })
export class TCurrencyPipe implements PipeTransform {
  private readonly lang = inject(LangService);
  transform(value: number, currency: string, options?: Intl.NumberFormatOptions, langOverride?: Lang): string {
    const lang = langOverride ?? this.lang.current;
    return formatCurrencyIntl(value, lang, currency, options);
  }
}
