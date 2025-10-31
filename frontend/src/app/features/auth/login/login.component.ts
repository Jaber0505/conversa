import {ChangeDetectionStrategy, Component, inject, Input} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TPipe } from '@core/i18n';
import { InputComponent, ButtonComponent } from '@shared';
import {AuthApiService, AuthTokenService} from "@core/http";
import {finalize, take} from "rxjs/operators";
import {ActivatedRoute, Router} from "@angular/router";

@Component({
  selector: 'app-auth-login',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TPipe,
    InputComponent,
    ButtonComponent,
  ],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AuthLoginComponent {
  email = '';
  password = '';
  loading = false;
  apiError: string | null = null;
  private _disabled = false;
  @Input() set disabled(v: boolean | null) { this._disabled = !!v; }
  get disabled() { return this._disabled; }

  private readonly authApi = inject(AuthApiService);
  private readonly userCache = inject(AuthTokenService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

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
        },
        error: (err) => {
          if (err?.status === 400 || err?.status === 401) {
            this.apiError = 'auth.errors.bad_credentials';
          } else {
            this.apiError = 'auth.errors.generic';
          }
        },
      });
  }
}
