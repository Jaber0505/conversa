import type { Lang } from './languages.config';

// Mapping locales régionales
const LOCALE_MAP: Record<Lang, string> = {
  fr: 'fr-BE',
  en: 'en-GB',
  nl: 'nl-BE',
};

// Fuseau par défaut (adapter si besoin)
const TZ = 'Europe/Brussels';

export function formatDateIntl(
  value: Date | string | number,
  lang: Lang,
  options: Intl.DateTimeFormatOptions = { dateStyle: 'medium' }
): string {
  if (value == null) return '';
  const d = value instanceof Date ? value : new Date(value);
  if (isNaN(+d)) return '';
  return new Intl.DateTimeFormat(LOCALE_MAP[lang] ?? lang, { timeZone: TZ, ...options }).format(d);
}

export function formatNumberIntl(
  value: number,
  lang: Lang,
  options: Intl.NumberFormatOptions = { maximumFractionDigits: 2 }
): string {
  if (value == null || isNaN(value as number)) return '';
  return new Intl.NumberFormat(LOCALE_MAP[lang] ?? lang, options).format(value);
}

export function formatCurrencyIntl(
  value: number,
  lang: Lang,
  currency: string,
  options: Intl.NumberFormatOptions = {}
): string {
  if (value == null || isNaN(value as number) || !currency) return '';
  return new Intl.NumberFormat(LOCALE_MAP[lang] ?? lang, { style: 'currency', currency, ...options }).format(value);
}
