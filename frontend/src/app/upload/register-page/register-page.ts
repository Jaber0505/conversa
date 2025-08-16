import { Component, ChangeDetectionStrategy } from '@angular/core';
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
  firstTabData?: FirstTabInfoModel;
  toNextTab(){
    this.cuurenTab = this.cuurenTab + 1
  }

  toPreviousTab(){
    this.cuurenTab = this.cuurenTab - 1
  }
  onFirstTabSuivant(data: FirstTabInfoModel) {
    this.firstTabData = data;
    console.log('Données du premier onglet :', this.firstTabData);

    // Ici, tu peux passer à l'onglet suivant, ou sauvegarder, etc.
  }

  onSecondTabSuivant( bio :  string ) {
    // ex: stocker, puis passer à l’onglet suivant
    // this.secondTabData = { bio };
    // this.currentTab = 2;
  }

  onThirdTabSuivant({ email, password }: { email: string; password: string }) {
    // ex: stocker puis passer à l’étape suivante
    // this.thirdTabData = { email, password };
    // this.currentTab = 3;
  }

}
