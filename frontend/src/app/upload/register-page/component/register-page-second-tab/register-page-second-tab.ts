import {Component, EventEmitter, Output} from '@angular/core';
import {FormsModule, NgForm} from "@angular/forms";
import {CommonModule} from "@angular/common";

@Component({
  selector: 'app-register-page-second-tab',
  imports: [
    FormsModule, CommonModule
  ],
  templateUrl: './register-page-second-tab.html',
  standalone: true,
  styleUrl: './register-page-second-tab.scss'
})
export class RegisterPageSecondTab {
  @Output() bioReturn = new EventEmitter<string>();

  bio: string = '';

  onNext(form?: NgForm) {
    const value = (this.bio ?? '').trim();
    if (form?.valid && value.length >= 10) {
      this.bioReturn.emit(value);
    }
  }
}
