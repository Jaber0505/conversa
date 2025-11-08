import {ChangeDetectionStrategy, ChangeDetectorRef, Component, inject, Input} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { TPipe } from '@core/i18n';
import { InputComponent, ButtonComponent } from '@shared';
import { ContainerComponent } from '@shared/layout/container/container.component';
import {AuthApiService, AuthTokenService} from "@core/http";
import { LangUtilsService, ErrorLoggerService, RateLimiterService } from '@app/core/services';
import { finalize, catchError, debounceTime } from "rxjs/operators";
import { EMPTY, Subject } from 'rxjs';
import {ActivatedRoute, Router, RouterModule} from "@angular/router";

@Component({
  selector: 'app-auth-login',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    TPipe,
    InputComponent,
    ButtonComponent,
    RouterModule,
    ContainerComponent,
  ],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AuthLoginComponent {
  loginForm: FormGroup;
  loading = false;
  apiError: string | null = null;
  showPassword = false;
  private _disabled = false;
  private submitSubject = new Subject<void>();

  @Input() set disabled(v: boolean | null) { this._disabled = !!v; }
  get disabled() { return this._disabled; }

  private readonly authApi = inject(AuthApiService);
  private readonly userCache = inject(AuthTokenService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly langUtils = inject(LangUtilsService);
  private readonly fb = inject(FormBuilder);
  private readonly errorLogger = inject(ErrorLoggerService);
  private readonly rateLimiter = inject(RateLimiterService);

  constructor() {
    this.loginForm = this.fb.group({
      email: ['', [Validators.required, Validators.email, Validators.maxLength(255)]],
      password: ['', [Validators.required, Validators.minLength(8), Validators.maxLength(128)]]
    });

    // Debounce sur submit avec 300ms
    this.submitSubject.pipe(
      debounceTime(300)
    ).subscribe(() => this.performLogin());

    // Clear error when form changes
    this.loginForm.valueChanges.subscribe(() => {
      if (this.apiError) {
        this.apiError = null;
        this.cdr.markForCheck();
      }
    });
  }

  getLang(): string {
    return this.langUtils.getLanguageFromRoute(this.route);
  }

  get emailControl() { return this.loginForm.get('email') as any; }
  get passwordControl() { return this.loginForm.get('password') as any; }

  get emailErrors(): string | null {
    const control = this.emailControl;
    if (!control?.touched || !control?.errors) return null;
    if (control.errors['required']) return 'auth.errors.email_required';
    if (control.errors['email']) return 'auth.errors.email_invalid';
    if (control.errors['maxLength']) return 'auth.errors.email_too_long';
    return null;
  }

  get passwordErrors(): string | null {
    const control = this.passwordControl;
    if (!control?.touched || !control?.errors) return null;
    if (control.errors['required']) return 'auth.errors.password_required';
    if (control.errors['minlength']) return 'auth.errors.password_too_short';
    if (control.errors['maxLength']) return 'auth.errors.password_too_long';
    return null;
  }

  onSubmit() {
    if (this.loginForm.invalid) {
      this.loginForm.markAllAsTouched();
      this.cdr.markForCheck();
      return;
    }
    if (this.loading) return; // Prevent double submit

    // Rate limiting check (sync with backend: 10 attempts/min)
    if (!this.rateLimiter.isAllowed('login')) {
      const timeUntilReset = this.rateLimiter.getTimeUntilReset('login');
      const secondsRemaining = Math.ceil(timeUntilReset / 1000);
      this.apiError = `auth.errors.rate_limit`;
      this.errorLogger.logWarn('Login rate limit exceeded', {
        remainingTime: secondsRemaining,
        component: 'AuthLoginComponent',
      });
      this.cdr.markForCheck();
      return;
    }

    this.submitSubject.next();
  }

  private performLogin() {
    this.loading = true;
    this.apiError = null;
    this.cdr.markForCheck();

    const { email, password } = this.loginForm.value;
    this.authApi
      .login({ email: email.trim().toLowerCase(), password })
      .pipe(
        catchError((err) => {
          // Log login error with context
          this.errorLogger.logError('Login failed', {
            email: email.trim().toLowerCase(),
            status: err?.status,
            component: 'AuthLoginComponent',
            remainingAttempts: this.rateLimiter.getRemainingAttempts('login'),
          });

          this.apiError = (err?.status === 400 || err?.status === 401)
            ? 'auth.errors.bad_credentials'
            : 'auth.errors.generic';
          this.cdr.markForCheck();
          return EMPTY;
        }),
        finalize(() => {
          this.loading = false;
          this.cdr.markForCheck();
        })
      )
      .subscribe({
        next: (res) => {
          this.errorLogger.logInfo('Login successful', { email: email.trim().toLowerCase() });
          this.rateLimiter.reset('login'); // Reset on successful login
          this.userCache.save(res.access, res.refresh);
          this.router.navigate(['/', this.getLang(), '']);
        },
      });
  }

  togglePassword() { this.showPassword = !this.showPassword; }
}

