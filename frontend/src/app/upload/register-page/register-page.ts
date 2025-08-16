import {Component, ChangeDetectionStrategy, inject} from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  RegisterPageFirstTab
} from "@app/upload/register-page/component/register-page-first-tab/register-page-first-tab";
import {
  RegisterPageSecondTab
} from "@app/upload/register-page/component/register-page-second-tab/register-page-second-tab";
import {
  RegisterPageThirdTab
} from "@app/upload/register-page/component/register-page-third-tab/register-page-third-tab";
import {FirstTabInfoModel} from "@app/upload/register-page/models/firstTabInfo.model";
import {TPipe} from "@core/i18n";
import {AuthApiService, AuthTokenService} from "@core/http";
import {finalize, take} from "rxjs/operators";
import {ActivatedRoute, Router} from "@angular/router";


@Component({
  selector: 'app-register-page',
  standalone: true,
  imports: [CommonModule, TPipe, RegisterPageFirstTab, RegisterPageSecondTab, RegisterPageThirdTab, TPipe],
  templateUrl: 'register-page.html',
  styleUrls: ['register-page.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RegisterPageComponent {

  constructor(private readonly authApi: AuthApiService,
              private readonly userCache: AuthTokenService) {}
  cuurenTab = 0;
  currentBio = "";
  firstTabData: FirstTabInfoModel = { prenom: '', nom: '', age: 0, target_langs : [], native_langs : []};
  private router = inject(Router);
  private route  = inject(ActivatedRoute);
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
    this.cuurenTab = this.cuurenTab - 1
  }
  onFirstTabSuivant(data: FirstTabInfoModel) {
    this.firstTabData = data;
    this.cuurenTab++;
  }

  onSecondTabSuivant( bio :  string ) {
    this.currentBio= bio;
    this.cuurenTab++;
  }

  onthirdTabPrevious( ) {
    this.cuurenTab--;
  }

  onThirdTabSuivant({ email, password }: { email: string; password: string }) {
    const registerData = {
      email,
      password,
      first_name: this.firstTabData.prenom,
      last_name: this.firstTabData.nom,
      bio: this.currentBio,
      native_langs: this.firstTabData.native_langs,
      target_langs: this.firstTabData.target_langs,
      consent_given: true,
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
                  this.apiError = 'auth.errors.bad_credentials'; // clé i18n
                } else {
                  this.apiError = 'auth.errors.generic'; // clé i18n
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
