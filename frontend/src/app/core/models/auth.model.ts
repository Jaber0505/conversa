// core/models/auth.model.ts
export type RegisterRequest = {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  birth_date: string;
  bio?: string;
  language_native: string;
  languages_spoken?: string[];
  languages_wanted?: string[];
  consent_given: boolean;
};

export type AuthResponse = {
  id: number;
  email: string;
  access: string;
  refresh: string;
};
