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
import {AuthApiService} from "@core/http";
import {finalize} from "rxjs/operators";
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
  cuurenTab = 0;
  currentBio = "";
  firstTabData: FirstTabInfoModel = { prenom: '', nom: '', age: 0, target_langs : [], native_langs : []};
  private router = inject(Router);
  private route  = inject(ActivatedRoute);

  toNextTab(){
    this.cuurenTab = this.cuurenTab + 1
  }
  private getLang(): string {
    // remonte la hiérarchie pour trouver :lang
    let r: ActivatedRoute | null = this.route;
    while (r) {
      const v = r.snapshot.paramMap.get('lang');
      if (v) return v;
      r = r.parent;
    }
    return 'fr';
  }
  constructor(private readonly authApi: AuthApiService) {}
  toPreviousTab(){
    // debugger;
    this.cuurenTab = this.cuurenTab - 1
  }
  onFirstTabSuivant(data: FirstTabInfoModel) {
    this.firstTabData = data;
    this.cuurenTab++;
  }

  onSecondTabSuivant( bio :  string ) {
    this.currentBio= bio;
    // debugger;
    this.cuurenTab++;
  }
  onSecondTabPrevious( bio :  string ) {
    // ex: stocker, puis passer à l’onglet suivant
    // this.secondTabData = { bio };
    // this.currentTab = 2;
    this.cuurenTab--;
  }

  onthirdTabPrevious( ) {
    // ex: stocker, puis passer à l’onglet suivant
    // this.secondTabData = { bio };
    // this.currentTab = 2;
    this.cuurenTab--;
  }

  onThirdTabSuivant({ email, password }: { email: string; password: string }) {
    const registerData = {
      email,
      password,
      first_name: this.firstTabData.prenom,
      last_name: this.firstTabData.nom,
      birth_date: "2000-08-16", // TODO: calculer à partir de l’âge ou champ date
      bio: this.currentBio,
      native_langs: this.firstTabData.native_langs,    // TODO: récupérer du formulaire
      target_langs: this.firstTabData.target_langs, // TODO: récupérer du formulaire
      consent_given: true,
      age : this.firstTabData.age
    } ;
debugger;
    this.authApi.register(registerData)
      .pipe(finalize(() => { /* ex: this.loading = false; */ }))
      .subscribe({
        next: () => {
          // ✅ succès → aller à /:lang/auth/login
          this.router.navigate(['/', this.getLang(), 'auth', 'login']);
        },
        error: (err) => {
          console.error('❌ Register failed', err);
          // ex: this.apiError = 'auth.errors.generic';
        }
      });
  }

}
