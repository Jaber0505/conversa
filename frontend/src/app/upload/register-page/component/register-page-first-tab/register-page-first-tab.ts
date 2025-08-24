import {Component, EventEmitter, Input, Output, OnInit, signal, computed} from '@angular/core';
import { FormsModule } from '@angular/forms';
import {InputComponent, SelectComponent, BadgeComponent, ButtonComponent, MultiSelectComponent} from '@shared';
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
    NavigationButtonsComponent, CommonModule, MultiSelectComponent
  ],
  templateUrl: './register-page-first-tab.html',
  styleUrls: ['./register-page-first-tab.scss']
})
export class RegisterPageFirstTab implements OnInit {
  @Input({ required: true }) firstTabInfo!: FirstTabInfoModel;
  @Output() suivant = new EventEmitter<FirstTabInfoModel>();
  langs: Option[] = [
    { value: 'fr', label: 'Français' },
    { value: 'nl', label: 'Nederlands' },
    { value: 'en', label: 'English' },
    { value: 'es', label: 'Español' },
    { value: 'de', label: 'Deutsch' },
    { value: 'ar', label: 'العربية' },
  ];
  pendingTargets: string[] = [];
  get pendingTarget(): string | null {
    return this.pendingTargets.length ? this.pendingTargets[0] : null;
  }
  onTargetsChange(values: string[]) {
    this.pendingTargets = values ?? [];
  }
  pendingNative?: string;
  //pendingTarget?: string;
  formSubmitted = false;

  ngOnInit() {
    this.firstTabInfo.native_langs ||= [];
    this.firstTabInfo.target_langs ||= [];
    if (this.pendingTargets.length === 0 && this.pendingTarget /* ancienne var */) {
      this.pendingTargets = [this.pendingTarget];
    }
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

  //addTarget() {
  //  const c = this.pendingTarget;
  //if (!c) return;
  // if (!this.firstTabInfo.target_langs.includes(c)) {
  //  this.firstTabInfo.target_langs = [...this.firstTabInfo.target_langs, c];
  //}
  //this.pendingTarget = undefined;
  //}
  removeTarget(code: string) {
    this.firstTabInfo.target_langs = this.firstTabInfo.target_langs.filter(x => x !== code);
  }

  displayLabel(options: Option[], value?: string) {
    return options.find(o => o.value === value)?.label ?? value;
  }

  onNext(): void {
    this.formSubmitted = true;
    if(this.firstTabInfo.prenom.length === 0 || this.firstTabInfo.nom.length === 0 || this.firstTabInfo.age < 18 ) return;
    else    this.suivant.emit(this.firstTabInfo); // le modèle contient déjà native_langs & target_langs
  }
}
