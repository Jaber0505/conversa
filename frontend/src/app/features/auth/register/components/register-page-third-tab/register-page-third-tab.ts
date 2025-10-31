import {Component, EventEmitter, Output, Input, OnInit} from '@angular/core';
import {ReactiveFormsModule, FormBuilder, FormGroup, Validators} from "@angular/forms";
import {CommonModule} from "@angular/common";
import {TPipe} from "@core/i18n";
import {InputComponent} from "@shared";
import {NavigationButtonsComponent} from "@shared/forms/navigation-button/navigation-buttons";

@Component({
  selector: 'app-register-page-third-tab',
  imports: [
    ReactiveFormsModule,
    CommonModule,
    TPipe,
    InputComponent,
    NavigationButtonsComponent
  ],
  templateUrl: './register-page-third-tab.html',
  standalone: true,
  styleUrl: './register-page-third-tab.scss'
})
export class RegisterPageThirdTab implements OnInit {
  thirdForm: FormGroup;
  showPassword = false;

  @Input() serverErrors: Partial<{ email: string[]; password: string[]; consent_given: string[] }> = {};
  @Input() loading = false;
  @Output() suivant = new EventEmitter<{ email: string; password: string, consent_given: boolean}>();
  @Output() previous = new EventEmitter();

  constructor(private fb: FormBuilder) {
    this.thirdForm = this.fb.group({
      email: ['', [Validators.required, Validators.email, Validators.maxLength(255)]],
      password: ['', [Validators.required, Validators.minLength(9), Validators.maxLength(128)]],
      consent_given: [false, [Validators.requiredTrue]]
    });
  }

  ngOnInit(): void {}

  get emailControl() { return this.thirdForm.get('email') as any; }
  get passwordControl() { return this.thirdForm.get('password') as any; }
  get consentControl() { return this.thirdForm.get('consent_given') as any; }

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
    if (control.errors['minlength']) return 'register.thirdTab.passwordLimit';
    if (control.errors['maxLength']) return 'auth.errors.password_too_long';
    return null;
  }

  get consentErrors(): string | null {
    const control = this.consentControl;
    if (!control?.touched || !control?.errors) return null;
    if (control.errors['required']) return 'register.thirdTab.consent_required';
    return null;
  }

  onNext(): void {
    if (this.thirdForm.invalid) {
      this.thirdForm.markAllAsTouched();
      return;
    }

    const { email, password, consent_given } = this.thirdForm.value;
    this.suivant.emit({
      email: email.trim().toLowerCase(),
      password,
      consent_given
    });
  }

  onPrevious() {
    this.previous.emit();
  }

  togglePassword() {
    this.showPassword = !this.showPassword;
  }
}
