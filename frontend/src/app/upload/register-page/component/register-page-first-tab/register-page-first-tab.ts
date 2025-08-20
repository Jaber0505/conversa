import { Component, EventEmitter, Input, Output, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { InputComponent, SelectComponent, BadgeComponent, ButtonComponent } from '@shared';
import { TPipe } from '@core/i18n';
import { NavigationButtonsComponent } from '@shared/forms/navigation-button/navigation-buttons';
import { FirstTabInfoModel } from '@app/upload/register-page/models/firstTabInfo.model';
import {CommonModule} from "@angular/common";

type Option = { value: string; label: string };

@Component({
  selector: 'app-register-page-first-tab',
  standalone: true,
  imports: [
    FormsModule, TPipe,
    InputComponent, SelectComponent, BadgeComponent, ButtonComponent,
    NavigationButtonsComponent,CommonModule
  ],
  templateUrl: './register-page-first-tab.html',
  styleUrls: ['./register-page-first-tab.scss']
})
export class RegisterPageFirstTab implements OnInit {
  @Input({ required: true }) firstTabInfo!: FirstTabInfoModel;
  @Output() suivant = new EventEmitter<FirstTabInfoModel>();
  firstNameErrorMessage = false;
  lastNameErrorMessage = false;
  ageErrorMessage = false;

  // Mock langues
  langs: Option[] = [
    { value: 'fr', label: 'Français' },
    { value: 'nl', label: 'Nederlands' },
    { value: 'en', label: 'English' },
    { value: 'es', label: 'Español' },
    { value: 'de', label: 'Deutsch' },
    { value: 'ar', label: 'العربية' },
  ];

  // Sélections en cours (via shared-select)
  pendingNative?: string;
  pendingTarget?: string;

  ngOnInit() {
    // Sécurise les tableaux si le parent ne les a pas initialisés
    this.firstTabInfo.native_langs ||= [];
    this.firstTabInfo.target_langs ||= [];
  }

  addNative() {
    const c = this.pendingNative;
    if (!c) return;
    if (!this.firstTabInfo.native_langs.includes(c)) {
      this.firstTabInfo.native_langs = [...this.firstTabInfo.native_langs, c];
    }
    this.pendingNative = undefined;
  }
  removeNative(code: string) {
    this.firstTabInfo.native_langs = this.firstTabInfo.native_langs.filter(x => x !== code);
  }

  addTarget() {
    const c = this.pendingTarget;
    if (!c) return;
    if (!this.firstTabInfo.target_langs.includes(c)) {
      this.firstTabInfo.target_langs = [...this.firstTabInfo.target_langs, c];
    }
    this.pendingTarget = undefined;
  }
  removeTarget(code: string) {
    this.firstTabInfo.target_langs = this.firstTabInfo.target_langs.filter(x => x !== code);
  }

  displayLabel(options: Option[], value?: string) {
    return options.find(o => o.value === value)?.label ?? value;
  }

  onNext(): void {
    if(!this.firstTabInfo.prenom) this.firstNameErrorMessage = true;
     if(!this.firstTabInfo.age) this.lastNameErrorMessage = true;
     if(!this.firstTabInfo.nom) this.ageErrorMessage = true;
if(!this.firstNameErrorMessage && !this.lastNameErrorMessage && !this.ageErrorMessage)    this.suivant.emit(this.firstTabInfo); // le modèle contient déjà native_langs & target_langs
  }
}
