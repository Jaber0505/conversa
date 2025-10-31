import {Component, ChangeDetectionStrategy, inject} from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  RegisterPageFirstTab
} from "./components/register-page-first-tab/register-page-first-tab";
import {
  RegisterPageSecondTab
} from "./components/register-page-second-tab/register-page-second-tab";
import {
  RegisterPageThirdTab
} from "./components/register-page-third-tab/register-page-third-tab";
import {FirstTabInfoModel} from "./models/firstTabInfo.model";
import {TPipe} from "@core/i18n";
import {AuthApiService, AuthTokenService} from "@core/http";
import { LangUtilsService, ErrorLoggerService, RateLimiterService } from '@app/core/services';
import {finalize, debounceTime} from "rxjs/operators";
import {ActivatedRoute, Router} from "@angular/router";
import { Subject } from 'rxjs';
@Component({
  selector: 'app-auth-register',
  standalone: true,
  imports: [CommonModule, TPipe, RegisterPageFirstTab, RegisterPageSecondTab, RegisterPageThirdTab],
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AuthRegisterComponent {
  private readonly authApi = inject(AuthApiService);
  private readonly userCache = inject(AuthTokenService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly langUtils = inject(LangUtilsService);
  private readonly errorLogger = inject(ErrorLoggerService);
  private readonly rateLimiter = inject(RateLimiterService);
  private submitSubject = new Subject<{ email: string; password: string; consent_given: boolean }>();

  currentTab = 0;
  currentBio = "";
  firstTabData: FirstTabInfoModel = { prenom: '', nom: '', age: 0, target_langs : [], native_langs : []};
  apiError: string | null = null;
  loading = false;

  // Server-side field errors per step
  firstTabErrors: Partial<{ prenom: string[]; nom: string[]; age: string[]; native_langs: string[]; target_langs: string[] }> = {};
  secondTabErrors: Partial<{ bio: string[] }> = {};
  thirdTabErrors: Partial<{ email: string[]; password: string[]; consent_given: string[] }> = {};

  constructor() {
    // Debounce register submission (300ms)
    this.submitSubject.pipe(
      debounceTime(300)
    ).subscribe((data) => this.performRegister(data));
  }

  private resetErrors() {
    this.apiError = null;
    this.firstTabErrors = {};
    this.secondTabErrors = {};
    this.thirdTabErrors = {};
  }

  private getLang(): string {
    return this.langUtils.getLanguageFromRoute(this.route);
  }

  onSecondTabPrevious(){
    this.currentTab = this.currentTab - 1
  }

  onFirstTabSuivant(data: FirstTabInfoModel) {
    this.firstTabData = data;
    this.currentTab++;
  }

  onSecondTabSuivant( bio :  string ) {
    this.currentBio= bio;
    this.currentTab++;
  }

  onthirdTabPrevious( ) {
    this.currentTab--;
  }

  onThirdTabSuivant({ email, password, consent_given }: { email: string; password: string; consent_given: boolean }) {
    // Rate limiting check (sync with backend: 5 registrations/hour)
    if (!this.rateLimiter.isAllowed('register')) {
      const timeUntilReset = this.rateLimiter.getTimeUntilReset('register');
      const minutesRemaining = Math.ceil(timeUntilReset / 60000);
      this.apiError = 'auth.errors.register_rate_limit';
      this.errorLogger.logWarn('Registration rate limit exceeded', {
        remainingTime: minutesRemaining,
        component: 'AuthRegisterComponent',
      });
      return;
    }

    if (this.loading) return; // Prevent double submit
    this.submitSubject.next({ email, password, consent_given });
  }

  private performRegister({ email, password, consent_given }: { email: string; password: string; consent_given: boolean }) {
    const registerData = {
      email,
      password,
      first_name: this.firstTabData.prenom,
      last_name: this.firstTabData.nom,
      bio: this.currentBio,
      native_langs: (this.firstTabData.native_langs || []).map(String),
      target_langs: (this.firstTabData.target_langs || []).map(String),
      consent_given: consent_given,
      age: Number(this.firstTabData.age)
    };

    this.resetErrors();
    this.loading = true;

    this.authApi.register(registerData)
      .pipe(finalize(() => { this.loading = false; }))
      .subscribe({
        next: () => {
          this.errorLogger.logInfo('Registration successful', { email });
          this.rateLimiter.reset('register'); // Reset on success

          // Auto-login after registration
          this.authApi
            .login({ email: (email || '').trim().toLowerCase(), password })
            .subscribe({
              next: (res) => {
                this.errorLogger.logInfo('Auto-login after registration successful', { email });
                this.userCache.save(res.access, res.refresh);
                this.router.navigate(['/', this.getLang(), '']);
              },
              error: (err) => {
                this.errorLogger.logError('Auto-login after registration failed', {
                  email,
                  status: err?.status,
                });
                if (err?.status === 400 || err?.status === 401) {
                  this.apiError = 'auth.errors.bad_credentials';
                } else {
                  this.apiError = 'auth.errors.generic';
                }
              },
            });
        },
        error: (err) => {
          this.errorLogger.logError('Registration failed', {
            email,
            status: err?.status,
            component: 'AuthRegisterComponent',
            remainingAttempts: this.rateLimiter.getRemainingAttempts('register'),
          });

          // Try to map server-side field errors to steps; fallback to generic error
          const e = err?.error;
          if (err?.status === 400 && e && typeof e === 'object' && !Array.isArray(e)) {
            // Map backend field names to our step fields
            this.firstTabErrors = {
              prenom: e.first_name,
              nom: e.last_name,
              age: e.age,
              native_langs: e.native_langs,
              target_langs: e.target_langs,
            };
            this.secondTabErrors = { bio: e.bio };
            this.thirdTabErrors = {
              email: e.email,
              password: e.password,
              consent_given: e.consent_given,
            };

            // Navigate to first step that has errors
            const hasFirst = Object.values(this.firstTabErrors).some(v => Array.isArray(v) ? v.length > 0 : !!v);
            const hasSecond = Object.values(this.secondTabErrors).some(v => Array.isArray(v) ? v.length > 0 : !!v);
            const hasThird = Object.values(this.thirdTabErrors).some(v => Array.isArray(v) ? v.length > 0 : !!v);
            if (hasFirst) this.currentTab = 0;
            else if (hasSecond) this.currentTab = 1;
            else if (hasThird) this.currentTab = 2;
            else this.apiError = e?.detail || 'auth.errors.generic';
          } else {
            this.apiError = e?.detail || 'auth.errors.generic';
          }
        }
      });
  }
}

