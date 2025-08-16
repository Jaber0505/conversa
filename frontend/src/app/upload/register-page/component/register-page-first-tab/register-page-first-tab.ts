import {Component, EventEmitter, Input, Output} from '@angular/core';
import {FirstTabInfoModel} from "@app/upload/register-page/models/firstTabInfo.model";
import {FormsModule} from "@angular/forms";
import {InputComponent} from "@shared";
import {TPipe} from "@core/i18n";
import {NavigationButtonsComponent} from "@shared/forms/navigation-button/navigation-buttons";

@Component({
  selector: 'app-register-page-first-tab',
  imports: [FormsModule, InputComponent, TPipe, NavigationButtonsComponent],
  templateUrl: './register-page-first-tab.html',
  standalone: true,
  styleUrl: './register-page-first-tab.scss'
})
export class RegisterPageFirstTab {
  @Input({ required: true }) firstTabInfo!: FirstTabInfoModel;
  @Output() suivant = new EventEmitter<FirstTabInfoModel>();

  onNext(): void {
    debugger;
    this.suivant.emit(this.firstTabInfo);
  }
}
