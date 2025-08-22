export type Language = {
  code: string;
  label_fr: string;
  label_en: string;
  label_nl: string;
  is_active?: boolean;
  sort_order?: number;
};
type UiLang = 'fr'|'en'|'nl';

export function langToOptionsSS(list: Language[], ui: string): { value: string; label: string }[] {
  const key = ui === 'fr' ? 'label_fr' : ui === 'en' ? 'label_en' : 'label_nl';
  return (list ?? [])
    .filter(l => l.is_active ?? true)
    .sort((a,b) => (a.sort_order ?? 999) - (b.sort_order ?? 999))
    .map(l => ({ value: l.code, label: l[key] as string }));
}
