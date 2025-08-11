import { Component, inject, signal, computed, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  FormBuilder,
  Validators,
  ReactiveFormsModule,
  AbstractControl,
  ValidatorFn,
} from '@angular/forms';
import { Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

import { TPipe } from '@app/core/i18n/t.pipe';
import { TAttrDirective } from '@app/core/i18n/t-attr.directive';

import { environment } from '@/environments/environment';
import { RegisterApiService } from '@app/core/api/register-api.service'; // ajuste si besoin

// -------- Types locaux (pour éviter les dépendances croisées) ----------
type Lang = { code: string; label: string };

export interface RegisterPayload {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  birth_date: string; // YYYY-MM-DD
  bio?: string;
  language_native: string;
  languages_spoken?: string[];
  languages_wanted?: string[];
  consent_given: boolean;
}

export interface AuthResponse {
  id: number;
  email: string;
  access: string;
  refresh: string;
}

type ProblemField = { field: string; code: string; params?: Record<string, unknown> };
type Problem = {
  status: number;
  code: string;
  detail?: string;
  fields?: ProblemField[];
};

// ---------------- Validators ----------------
function minAgeValidator(minYears: number): ValidatorFn {
  return (control: AbstractControl) => {
    const v: string | null = control.value;
    if (!v) return { minAge: { requiredAge: minYears } };

    const parts = v.split('-').map(Number);
    if (parts.length !== 3 || parts.some(isNaN)) return { minAge: { requiredAge: minYears } };

    const [y, m, d] = parts;
    const today = new Date();
    let age = today.getFullYear() - y;
    if (today.getMonth() + 1 < m || (today.getMonth() + 1 === m && today.getDate() < d)) {
      age--;
    }
    return age >= minYears ? null : { minAge: { requiredAge: minYears } };
  };
}

// ------------- Fallback langues si l’API tombe -------------
const MOCK_LANGS: Lang[] = [
  { code: 'fr', label: 'Français' },
  { code: 'nl', label: 'Nederlands' },
  { code: 'en', label: 'English' },
  { code: 'es', label: 'Español' },
  { code: 'de', label: 'Deutsch' },
  { code: 'it', label: 'Italiano' },
  { code: 'pt', label: 'Português' },
  { code: 'ar', label: 'العربية' },
  { code: 'zh', label: '中文' },
];

@Component({
  selector: 'app-register-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, TPipe, TAttrDirective],
  templateUrl: './register-page.component.html',
})
export class RegisterPageComponent {
  // DI
  private fb = inject(FormBuilder);
  private http = inject(HttpClient);
  private api = inject(RegisterApiService);
  private router = inject(Router);

  // Etapes & progression
  readonly totalSteps = 4; // 1: identité, 2: bio, 3: langues, 4: identifiants
  step = signal(1);
  canGoBack = computed(() => this.step() > 1);
  canGoNext = computed(() => this.step() < this.totalSteps);

  // UI state
  submitted = false;
  isSubmitting = false;
  globalErrorKey: string | null = null; // clé i18n, ex: 'auth.register.errors.generic'

  // Langues
  languages: Lang[] = [];
  isLoadingLangs = false;

  // Erreurs serveur par champ (optionnel si tu veux les lire dans le template)
  serverErrors = signal<Record<string, string>>({});

  // Formulaire (groupé par étape)
  form = this.fb.group({
    identity: this.fb.group({
      first_name: ['', [Validators.required, Validators.maxLength(150)]],
      last_name: ['', [Validators.required, Validators.maxLength(150)]],
      birth_date: ['', [Validators.required, minAgeValidator(18)]],
    }),
    bio: this.fb.group({
      bio: ['', [Validators.maxLength(1000)]],
    }),
    languages: this.fb.group({
      language_native: ['', Validators.required],
      languages_spoken: this.fb.control<string[]>([]),
      languages_wanted: this.fb.control<string[]>([]),
    }),
    credentials: this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(8)]],
      consent_given: [false, [Validators.requiredTrue]],
    }),
  });

  // Raccourcis
  get fIdentity() { return this.form.get('identity') as any; }
  get fBio() { return this.form.get('bio') as any; }
  get fLang() { return this.form.get('languages') as any; }
  get fCred() { return this.form.get('credentials') as any; }

  constructor() {
    this.loadLanguages();

    // On efface les erreurs globales/champ quand on change d’étape
    effect(() => {
      void this.step();
      this.serverErrors.set({});
      this.globalErrorKey = null;
    });
  }

  // -------- Navigation --------
  next(): void {
    const grp = this.currentGroup();
    this.submitted = true;

    if (!grp) return;
    if (grp.invalid) {
      grp.markAllAsTouched();
      return;
    }
    this.submitted = false;
    if (this.step() < this.totalSteps) this.step.update((s) => s + 1);
  }

  back(): void {
    this.submitted = false;
    if (this.step() > 1) this.step.update((s) => s - 1);
  }

  private currentGroup() {
    switch (this.step()) {
      case 1: return this.fIdentity;
      case 2: return this.fBio;
      case 3: return this.fLang;
      case 4: return this.fCred;
      default: return null;
    }
  }

  // -------- Chargement des langues (API -> fallback) --------
  private loadLanguages(): void {
    this.isLoadingLangs = true;

    const base = (environment as any)?.apiBaseUrl ?? (environment as any)?.apiUrl ?? '';
    this.http.get<{ results: Lang[] }>(`${base}/languages/`)
      .pipe(
        map((r) => r?.results ?? []),
        catchError(() => of(MOCK_LANGS)),
      )
      .subscribe((list) => {
        this.languages = list;
        this.isLoadingLangs = false;
      });
  }

  // -------- Soumission finale --------
  submit(): void {
    // Valide tous les groupes
    this.submitted = true;
    Object.values(this.form.controls).forEach((g) => g.markAllAsTouched());
    if (this.form.invalid) return;

    const payload: RegisterPayload = {
      email: this.fCred.get('email')!.value!,
      password: this.fCred.get('password')!.value!,
      first_name: this.fIdentity.get('first_name')!.value!,
      last_name: this.fIdentity.get('last_name')!.value!,
      birth_date: this.fIdentity.get('birth_date')!.value!, // YYYY-MM-DD
      bio: this.fBio.get('bio')!.value ?? '',
      language_native: this.fLang.get('language_native')!.value!,
      languages_spoken: this.fLang.get('languages_spoken')!.value ?? [],
      languages_wanted: this.fLang.get('languages_wanted')!.value ?? [],
      consent_given: this.fCred.get('consent_given')!.value === true,
    };

    this.isSubmitting = true;
    this.globalErrorKey = null;

    this.api.register(payload)
      .pipe(
        catchError((err: any) => {
          this.isSubmitting = false;
          const problem: Problem | undefined = err?.error ?? err;
          this.applyProblemErrors(problem);
          return of(null);
        })
      )
      .subscribe((res) => {
        if (!res) return;
        const data = res as AuthResponse;

        // Stockage simple — tu pourras déplacer ça dans un AuthService dédié
        localStorage.setItem('access', data.access);
        localStorage.setItem('refresh', data.refresh);

        this.router.navigateByUrl('/'); // cible à ajuster
      });
  }

  // -------- Mapping des erreurs problem+json -> form --------
  private applyProblemErrors(problem?: Problem) {
    const fields = problem?.fields ?? [];
    const byField: Record<string, string> = {};

    const mapPath: Record<string, string> = {
      // backend -> chemin form
      first_name: 'identity.first_name',
      last_name: 'identity.last_name',
      birth_date: 'identity.birth_date',
      bio: 'bio.bio',
      language_native: 'languages.language_native',
      languages_spoken: 'languages.languages_spoken',
      languages_wanted: 'languages.languages_wanted',
      email: 'credentials.email',
      password: 'credentials.password',
      consent_given: 'credentials.consent_given',
    };

    if (fields.length) {
      for (const f of fields) {
        const path = mapPath[f.field] ?? f.field;
        const c = this.form.get(path);
        if (c) {
          c.setErrors({ ...(c.errors ?? {}), server: f.code || 'INVALID' });
        }
        byField[f.field] = f.code || 'INVALID';
      }
      this.serverErrors.set(byField);
      return;
    }

    // Erreur globale → clé i18n générique
    // (Tu peux affiner avec un switch sur problem.code si besoin)
    this.globalErrorKey = 'auth.register.errors.generic';
  }

  // -------- Helpers sélection multiple langues --------
  onToggleLang(ctrlKey: 'languages_spoken' | 'languages_wanted', code: string, checked: boolean) {
    const ctrl = this.fLang.get(ctrlKey);
    if (!ctrl) return;
    const set = new Set<string>(ctrl.value ?? []);
    checked ? set.add(code) : set.delete(code);
    ctrl.setValue([...set]);
    ctrl.markAsDirty();
  }
}
