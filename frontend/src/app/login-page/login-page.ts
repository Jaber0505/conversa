import {ChangeDetectionStrategy, Component, EventEmitter, inject, Input, Output} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TPipe } from '@core/i18n';
import { InputComponent, ButtonComponent } from '@shared';
import {AuthApiService, AuthTokenService} from "@core/http";
import {finalize, take} from "rxjs/operators";
import {ActivatedRoute, Router} from "@angular/router";

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
  private _disabled = false;
  @Input() set disabled(v: boolean | null) { this._disabled = !!v; }
  get disabled() { return this._disabled; }
  constructor(
    private readonly authApi: AuthApiService,
    private readonly userCache: AuthTokenService
  ) {}
  private router = inject(Router);
  private route  = inject(ActivatedRoute);

  private getLang(): string {
    let r: ActivatedRoute | null = this.route;
    while (r) {
      const v = r.snapshot.paramMap.get('lang');
      if (v) return v;
      r = r.parent;
    }
    return 'fr';
  }
  onSubmit() {
    this.authApi
      .login({ email: (this.email || '').trim(), password: this.password })
      .pipe(take(1), finalize(() => (this.loading = false)))
      .subscribe({
        next: (res) => {
          this.userCache.save(res.access, res.refresh);
          this.userCache.access;
          this.router.navigate(['/', this.getLang(), '']);
          // this.loginSuccess.emit(res);
        },
        error: (err) => {
          if (err?.status === 400 || err?.status === 401) {
            this.apiError = 'auth.errors.bad_credentials'; // clé i18n
          } else {
            this.apiError = 'auth.errors.generic'; // clé i18n
          }
        },
      });
  }
}
