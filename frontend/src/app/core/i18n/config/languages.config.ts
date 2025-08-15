export const SUPPORTED_LANGS = ['fr', 'en', 'nl'] as const;
export type Lang = typeof SUPPORTED_LANGS[number];

export const DEFAULT_LANGUAGE: Lang = 'fr';
export const STORAGE_KEY = 'app.lang';
