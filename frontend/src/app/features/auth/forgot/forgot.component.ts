import { ChangeDetectionStrategy, ChangeDetectorRef, Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { TPipe } from '@core/i18n';
import { InputComponent, ButtonComponent } from '@shared';
import { AuthApiService } from '@core/http';
import { ActivatedRoute, Router } from '@angular/router';
import { ContainerComponent } from "@shared/layout/container/container.component";
import { LandingHeaderComponent } from "@shared/components/landing-header/landing-header.component";
import { ErrorLoggerService } from '@app/core/services';
import { debounceTime } from 'rxjs/operators';
import { Subject } from 'rxjs';

@Component({
  selector: 'app-auth-forgot',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, TPipe, InputComponent, ButtonComponent, ContainerComponent, LandingHeaderComponent],
  templateUrl: './forgot.component.html',
  styleUrls: ['./forgot.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ForgotPasswordComponent {
  forgotForm: FormGroup;
  sent = false;
  loading = false;
  private readonly authApi = inject(AuthApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly fb = inject(FormBuilder);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly errorLogger = inject(ErrorLoggerService);
  private submitSubject = new Subject<void>();

  constructor() {
    this.forgotForm = this.fb.group({
      email: ['', [Validators.required, Validators.email, Validators.maxLength(255)]]
    });

    // Debounce submit (300ms)
    this.submitSubject.pipe(
      debounceTime(300)
    ).subscribe(() => this.performSubmit());
  }

  get lang(): string { return this.route.snapshot.paramMap.get('lang') ?? 'fr'; }

  get emailControl() { return this.forgotForm.get('email') as any; }

  get emailErrors(): string | null {
    const control = this.emailControl;
    if (!control?.touched || !control?.errors) return null;
    if (control.errors['required']) return 'auth.errors.email_required';
    if (control.errors['email']) return 'auth.errors.email_invalid';
    if (control.errors['maxLength']) return 'auth.errors.email_too_long';
    return null;
  }

  submit() {
    if (this.forgotForm.invalid) {
      this.forgotForm.markAllAsTouched();
      this.cdr.markForCheck();
      return;
    }
    if (this.loading) return;
    this.submitSubject.next();
  }

  private performSubmit() {
    const email = this.forgotForm.value.email.trim().toLowerCase();
    this.loading = true;
    this.cdr.markForCheck();

    this.authApi.requestPasswordReset(email).subscribe({
      next: () => {
        this.errorLogger.logInfo('Password reset requested', { email });
        this.sent = true;
        this.loading = false;
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.errorLogger.logWarn('Password reset request completed (error hidden for security)', {
          email,
          status: err?.status,
        });
        // Always show success message for security (don't reveal if email exists)
        this.sent = true;
        this.loading = false;
        this.cdr.markForCheck();
      },
    });
  }

  backToLogin() { this.router.navigate(['/', this.lang, 'auth', 'login']); }
}
