import {Component, EventEmitter, Input, Output, OnInit, signal, computed, inject} from '@angular/core';
import { FormsModule } from '@angular/forms';
import {InputComponent, SelectComponent, BadgeComponent, ButtonComponent, MultiSelectComponent} from '@shared';
import { TPipe } from '@core/i18n';
import { NavigationButtonsComponent } from '@shared/forms/navigation-button/navigation-buttons';
import { FirstTabInfoModel } from '@app/upload/register-page/models/firstTabInfo.model';
import {CommonModule} from "@angular/common";
import {SelectOption} from "@shared/forms/select/select.component";
import {LanguagesApiService} from "@core/http";
import {langToOptionsSS, Language} from "@core/models";

type Option = { value: string; label: string };

@Component({
  selector: 'app-register-page-first-tab',
  standalone: true,
  imports: [
    FormsModule, TPipe,
    InputComponent, MultiSelectComponent,
    NavigationButtonsComponent, CommonModule, MultiSelectComponent, MultiSelectComponent
  ],
  templateUrl: './register-page-first-tab.html',
  styleUrls: ['./register-page-first-tab.scss']
})
export class RegisterPageFirstTab implements OnInit {
  @Input({ required: true }) firstTabInfo!: FirstTabInfoModel;
  @Output() suivant = new EventEmitter<FirstTabInfoModel>();

  uiLang: string | null = 'fr';
  onTargetsChange(values: string[]) {
    this.firstTabInfo.target_langs = values ?? [];
  }
  onNativeChange(values: string[]) {
    this.firstTabInfo.native_langs = values ?? [];
  }
  langOptions = signal<SelectOption[]>([]);
  formNotValid = false;
  allLanguage: Language[] = [];
  private languagesApiService = inject(LanguagesApiService);
  ngOnInit() {
    this.firstTabInfo.native_langs ||= [];
    this.firstTabInfo.target_langs ||= [];
    this.languagesApiService.list().subscribe((paginatedLanguage =>{
      this.allLanguage = paginatedLanguage.results;
      this.langOptions.set(langToOptionsSS(this.allLanguage, this.uiLang!));
    }))
  }
  onNext(): void {
    if(this.firstTabInfo.prenom.length === 0 || this.firstTabInfo.nom.length === 0 || this.firstTabInfo.age < 18 || this.firstTabInfo.target_langs.length===0 || this.firstTabInfo.native_langs.length===0 ) this.formNotValid = true;
    else    this.suivant.emit(this.firstTabInfo);
  }
}
