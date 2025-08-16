import {ChangeDetectionStrategy, Component, EventEmitter, Input, Output} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TPipe } from '@core/i18n';
import { InputComponent, ButtonComponent } from '@shared';
import { NavigationButtonsComponent } from '@shared/forms/navigation-button/navigation-buttons';
import {AuthApiService, AuthTokenService} from "@core/http";
import {finalize, take} from "rxjs/operators";

@Component({
  selector: 'app-login-page',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TPipe,
    InputComponent,
    ButtonComponent,
  ],
  templateUrl: './login-page.html',
  styleUrls: ['./login-page.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LoginPageComponent {
  email = '';
  password = '';
  loading = false;
  apiError: string | null = null;
  @Output() previous = new EventEmitter<void>();
  // @Output() login = new EventEmitter<{ email: string; password: string }>();
  @Output() loginSuccess = new EventEmitter();
  @Output() loginFailure = new EventEmitter<any>();
  private _disabled = false;
  @Input() set disabled(v: boolean | null) { this._disabled = !!v; }
  get disabled() { return this._disabled; }
  constructor(
    private readonly authApi: AuthApiService,
    private readonly userCache: AuthTokenService
  ) {}
  onSubmit() {
    // this.login.emit({
    //   email: (this.email || '').trim(),
    //   password: this.password,
    // });

    this.authApi
      .login({ email: (this.email || '').trim(), password: this.password })
      .pipe(take(1), finalize(() => (this.loading = false)))
      .subscribe({
        next: (res) => {
          // À toi de décider : stocker les tokens ici, ou remonter au parent
          // localStorage.setItem('access', res.access);
          // localStorage.setItem('refresh', res.refresh);
          this.userCache.save(res.access, res.refresh);
          this.userCache.access;
          debugger;
          this.loginSuccess.emit(res);
        },
        error: (err) => {
          // Messages d’erreurs simples et propres
          if (err?.status === 400 || err?.status === 401) {
            this.apiError = 'auth.errors.bad_credentials'; // clé i18n
          } else {
            this.apiError = 'auth.errors.generic'; // clé i18n
          }
          this.loginFailure.emit(err);
        },
      });
  }
  onPrevious() { this.previous.emit(); }
}
