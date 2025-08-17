import {Component, EventEmitter, Output} from '@angular/core';
import {FormsModule} from "@angular/forms";
import {CommonModule, JsonPipe} from "@angular/common";
import {TPipe} from "@core/i18n";
import {ButtonComponent, InputComponent} from "@shared";
import {NavigationButtonsComponent} from "@shared/forms/navigation-button/navigation-buttons";

@Component({
  selector: 'app-register-page-third-tab',
    imports: [
        FormsModule,
        JsonPipe, CommonModule, TPipe, InputComponent, NavigationButtonsComponent, ButtonComponent
    ],
  templateUrl: './register-page-third-tab.html',
  standalone: true,
  styleUrl: './register-page-third-tab.scss'
})
export class RegisterPageThirdTab {
  email = '';
  password = '';
  consent_given = false;

  @Output() suivant = new EventEmitter<{ email: string; password: string,  consent_given: boolean}>();
  @Output() previous = new EventEmitter();
  onNext(): void {
    if (!this.consent_given) return;
    this.suivant.emit({ email: (this.email || '').trim(), password: this.password, consent_given: this.consent_given });
  }
  onPrevious() {
    this.previous.emit();
  }
}
