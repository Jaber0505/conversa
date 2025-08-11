import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  FormBuilder,
  Validators,
  ReactiveFormsModule,
  AbstractControl,
  ValidatorFn,
  FormGroup,
} from '@angular/forms';
import { Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

import { environment } from 'src/environments/environment';
import {
  RegisterApiService,
  type RegisterPayload,
  type AuthResponse,
  type Problem,
} from '@app/core/api/register-api.service';

// --- Types UI ---
type Lang = { code: string; label: string };

// --- Validator min âge ---
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

// --- Fallback langues si l'API échoue ---
const MOCK_LANGS: Lang[] = [
  { code: 'fr', label: 'Français' },
  { code: 'nl', label: 'Néerlandais' },
  { code: 'en', label: 'Anglais' },
  { code: 'it', label: 'Italien' },
  { code: 'de', label: 'Allemand' },
  { code: 'ar', label: 'Arabe' },
  { code: 'zh', label: 'Chinois' },
  { code: 'pt', label: 'Portugais' },
  { code: 'es', label: 'Espagnol' },
];

@Component({
  selector: 'app-register-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './register-page.component.html',
  styleUrls: ['./register-page.component.scss'],
})
export class RegisterPageComponent {
  // DI
  private fb = inject(FormBuilder);
  private http = inject(HttpClient);
  private api = inject(RegisterApiService);
  private router = inject(Router);

  // Étapes
  totalSteps = 4; // 1: identité, 2: bio, 3: identifiants, 4: langues
  step = 1;

  // État UI
  submitting = false;
  submitted = false; // déclenche l’affichage des erreurs requises
  isLoadingLangs = false;
  globalErrorKey: string | null = null;

  // Données
  languages: Lang[] = [];

  // Erreurs serveur par champ (clés i18n)
  serverErrors: Record<string, string> = {};

  // Formulaires (groupés par étape)
  form = this.fb.group({
    identity: this.fb.group({
      first_name: ['', [Validators.required, Validators.maxLength(150)]],
      last_name: ['', [Validators.required, Validators.maxLength(150)]],
      birth_date: ['', [Validators.required, minAgeValidator(18)]],
    }),
    bio: this.fb.group({
      bio: ['', [Validators.maxLength(1000)]],
    }),
    credentials: this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(8)]],
      consent_given: [false, [Validators.requiredTrue]],
    }),
    languages: this.fb.group({
      language_native: ['', Validators.required],
      languages_spoken: this.fb.control<string[]>([]),
      languages_wanted: this.fb.control<string[]>([]),
    }),
  });

  // Raccourcis
  get fIdentity(): FormGroup { return this.form.get('identity') as FormGroup; }
  get fBio(): FormGroup { return this.form.get('bio') as FormGroup; }
  get fCred(): FormGroup { return this.form.get('credentials') as FormGroup; }
  get fLang(): FormGroup { return this.form.get('languages') as FormGroup; }

  // Progress %
  get progressPercent(): number {
    return Math.round((this.step / this.totalSteps) * 100);
  }

  constructor() {
    this.loadLanguages();
  }

  // --- Navigation ---
  goNext(): void {
    const current = this.currentGroup();
    if (!current) return;

    if (current.invalid) {
      current.markAllAsTouched();
      return;
    }
    if (this.step < this.totalSteps) {
      this.serverErrors = {};
      this.globalErrorKey = null;
      this.step += 1;
    }
  }

  goPrev(): void {
    if (this.step > 1) {
      this.serverErrors = {};
      this.globalErrorKey = null;
      this.step -= 1;
    }
  }

  private currentGroup(): FormGroup | null {
    switch (this.step) {
      case 1: return this.fIdentity;
      case 2: return this.fBio;
      case 3: return this.fCred;
      case 4: return this.fLang;
      default: return null;
    }
  }

  // --- Langues (API → fallback) ---
  private loadLanguages(): void {
    this.isLoadingLangs = true;
    this.http.get<{ results: Lang[] }>(`${environment.apiBaseUrl}/languages/`)
      .pipe(
        map(r => r?.results ?? []),
        catchError(() => of(MOCK_LANGS)),
      )
      .subscribe(list => {
        this.languages = list;
        this.isLoadingLangs = false;
      });
  }

  // --- Soumission finale ---
  onSubmit(): void {
    this.submitted = true;
    // tout valider
    Object.values(this.form.controls).forEach((g) => (g as FormGroup).markAllAsTouched());
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

    this.submitting = true;
    this.form.disable();

    this.api.register(payload)
      .pipe(
        catchError((err: any) => {
          this.form.enable();
          this.submitting = false;
          const problem: Problem | undefined = err?.error ?? err;
          this.applyProblemErrors(problem);
          return of(null);
        })
      )
      .subscribe((res) => {
        if (!res) return;
        const data = res as AuthResponse;
        localStorage.setItem('access', data.access);
        localStorage.setItem('refresh', data.refresh);
        this.router.navigateByUrl('/');
      });
  }

  // --- Mapping erreurs backend -> clés i18n + erreurs controls ---
  private applyProblemErrors(problem?: Problem) {
    const fields = problem?.fields ?? [];
    const byField: Record<string, string> = {};

    const pathMap: Record<string, string> = {
      email: 'credentials.email',
      password: 'credentials.password',
      consent_given: 'credentials.consent_given',
      first_name: 'identity.first_name',
      last_name: 'identity.last_name',
      birth_date: 'identity.birth_date',
      language_native: 'languages.language_native',
      languages_spoken: 'languages.languages_spoken',
      languages_wanted: 'languages.languages_wanted',
      bio: 'bio.bio',
    };

    for (const f of fields) {
      const path = pathMap[f.field] ?? f.field;
      const c = this.form.get(path);
      const key = this.codeToKey(f.code);
      if (c) {
        c.setErrors({ ...(c.errors ?? {}), serverKey: key });
      }
      byField[f.field] = key;
    }

    if (!fields.length) {
      this.globalErrorKey = this.codeToKey(problem?.code) || 'problem.unknown';
    } else {
      this.globalErrorKey = null;
    }

    this.serverErrors = byField;
  }

  private codeToKey(code?: string): string {
    if (!code) return 'problem.unknown';
    const known: Record<string, string> = {
      VALIDATION_ERROR: 'problem.validation',
      LOGIN_FAILED: 'auth.errors.login_failed',
      USER_DISABLED: 'auth.errors.user_disabled',
      CONSENT_REQUIRED: 'register.errors.consent_required',
      AGE_MIN: 'register.errors.age_min',
      TOKEN_INVALID: 'auth.errors.token_invalid',
      TOKEN_REQUIRED: 'auth.errors.token_required',
    };
    return known[code] ?? `problem.${String(code).toLowerCase()}`;
  }

  // --- Checkbox “chips” langues ---
  onToggleLang(listName: 'languages_spoken' | 'languages_wanted', code: string, checked: boolean) {
    const ctrl = this.fLang.get(listName);
    if (!ctrl) return;
    const arr = new Set<string>(ctrl.value ?? []);
    if (checked) arr.add(code); else arr.delete(code);
    ctrl.setValue([...arr]);
    ctrl.markAsDirty();
  }
}
