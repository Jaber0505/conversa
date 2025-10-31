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
import {finalize} from "rxjs/operators";
import {ActivatedRoute, Router} from "@angular/router";


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

  currentTab = 0;
  currentBio = "";
  firstTabData: FirstTabInfoModel = { prenom: '', nom: '', age: 0, target_langs : [], native_langs : []};
  apiError: string | null = null;

  private getLang(): string {
    let r: ActivatedRoute | null = this.route;
    while (r) {
      const v = r.snapshot.paramMap.get('lang');
      if (v) return v;
      r = r.parent;
    }
    return 'fr';
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
    const registerData = {
      email,
      password,
      first_name: this.firstTabData.prenom,
      last_name: this.firstTabData.nom,
      bio: this.currentBio,
      native_langs: this.firstTabData.native_langs,
      target_langs: this.firstTabData.target_langs,
      consent_given: consent_given,
      age : this.firstTabData.age
    } ;
    this.authApi.register(registerData)
      .pipe(finalize(() => { /* ex: this.loading = false; */ }))
      .subscribe({
        next: () => {
          this.authApi
            .login({ email: (email || '').trim(), password })
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
          this.router.navigate(['/', this.getLang(), 'auth', 'login']);
        },
        error: (err) => {
          console.error('❌ Register failed', err);
        }
      });
  }
}
