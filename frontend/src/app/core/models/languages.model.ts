export type Language = {
  code: string;           // ex: "fr", "en"
  label_fr: string;
  label_en: string;
  label_nl: string;
  is_active?: boolean;
  sort_order?: number;
};
