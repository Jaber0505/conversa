import {Component, EventEmitter, Input, Output} from '@angular/core';
import {FormsModule, NgForm} from "@angular/forms";
import {CommonModule} from "@angular/common";
import {TPipe} from "@core/i18n";
import {NavigationButtonsComponent} from "@shared/forms/navigation-button/navigation-buttons";

@Component({
  selector: 'app-register-page-second-tab',
  imports: [
    FormsModule, CommonModule, TPipe, NavigationButtonsComponent
  ],
  templateUrl: './register-page-second-tab.html',
  standalone: true,
  styleUrl: './register-page-second-tab.scss'
})
export class RegisterPageSecondTab {
  @Output() bioReturn = new EventEmitter<string>();
  @Input({ required: true }) currentBio!: string;
  @Output() previous = new EventEmitter();

  bio: string = '';
  formNotValid = false;
  onNext(form?: NgForm) {
    const value = (this.currentBio ?? '').trim();
    if(this.currentBio.length===0) this.formNotValid =true;
    else
      this.bioReturn.emit(value);
  }
  onPrevious() {
      this.previous.emit();
  }

}
