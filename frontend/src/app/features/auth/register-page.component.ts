import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { RegisterApiService, RegisterPayload } from './register-api.service';

// i18n
import { TPipe } from '@app/core/i18n/t.pipe';
import { TAttrDirective } from '@app/core/i18n/t-attr.directive';
import { I18nService } from '@app/core/i18n/i18n.service';

type RegisterErrKey =
  | 'email' | 'password' | 'first_name' | 'last_name'
  | 'birth_date' | 'bio' | 'language_native'
  | 'languages_spoken' | 'consent_given';

@Component({
  standalone: true,
  selector: 'app-register-page',
  imports: [CommonModule, ReactiveFormsModule, RouterLink, TPipe, TAttrDirective],
  templateUrl: './register-page.component.html',
  styleUrls: ['./register-page.component.scss'],
})
export class RegisterPageComponent {
  private fb = inject(FormBuilder);
  private api = inject(RegisterApiService);
  private i18n = inject(I18nService);

  loading = false;
  globalMsg = '';
  successEmail = '';

  // Typage strict → autorise la dot-notation dans le template
  err: Partial<Record<RegisterErrKey, string>> = {};

  // Laisse Angular inférer les types via nonNullable.control(...)
  form = this.fb.nonNullable.group({
    email:                this.fb.nonNullable.control('', { validators: [Validators.required, Validators.email] }),
    password:             this.fb.nonNullable.control('', { validators: [Validators.required, Validators.minLength(8)] }),
    first_name:           this.fb.nonNullable.control('', { validators: [Validators.required] }),
    last_name:            this.fb.nonNullable.control('', { validators: [Validators.required] }),
    birth_date:           this.fb.nonNullable.control('', { validators: [Validators.required] }), // yyyy-mm-dd
    bio:                  this.fb.nonNullable.control(''),
    language_native:      this.fb.nonNullable.control('fr', { validators: [Validators.required] }),
    languages_spoken_csv: this.fb.nonNullable.control('en,nl'),
    consent_given:        this.fb.nonNullable.control(false, { validators: [Validators.requiredTrue] }),
  });

  submit() {
    if (this.loading || this.form.invalid) return;

    this.loading = true;
    this.err = {};
    this.globalMsg = '';
    this.successEmail = '';

    const v = this.form.getRawValue(); // types non-nulls inférés

    const payload: RegisterPayload = {
      email: v.email,
      password: v.password,
      first_name: v.first_name,
      last_name: v.last_name,
      birth_date: v.birth_date,
      bio: v.bio ?? '',
      language_native: v.language_native,
      languages_spoken: (v.languages_spoken_csv ?? '')
        .split(',').map(s => s.trim()).filter(Boolean),
      consent_given: v.consent_given,
    };

    this.api.register(payload).subscribe({
      next: (res) => {
        this.loading = false;
        this.successEmail = res.email;
        this.globalMsg = this.i18n.t('auth.register.success');
      },
      error: (err) => {
        this.loading = false;
        const p = (err && err.error) ? err.error as {
          code?: string;
          params?: Record<string, any>;
          fields?: Array<{ field: RegisterErrKey; code: string; params?: Record<string, any> }>;
        } : {};

        this.globalMsg = this.i18n.t(`errors.${p.code ?? 'UNSPECIFIED_ERROR'}`, p.params);

        if (Array.isArray(p.fields)) {
          for (const f of p.fields) {
            if (!f?.field) continue;
            this.err[f.field] = this.i18n.t(`errors.${f.code}`, f.params);
          }
        }
      }
    });
  }
}
