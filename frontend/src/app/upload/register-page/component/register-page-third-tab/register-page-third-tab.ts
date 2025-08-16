import {Component, EventEmitter, Output} from '@angular/core';
import {FormsModule} from "@angular/forms";
import {CommonModule, JsonPipe} from "@angular/common";

@Component({
  selector: 'app-register-page-third-tab',
  imports: [
    FormsModule,
    JsonPipe, CommonModule
  ],
  templateUrl: './register-page-third-tab.html',
  standalone: true,
  styleUrl: './register-page-third-tab.scss'
})
export class RegisterPageThirdTab {
  email = '';
  password = '';

  @Output() suivant = new EventEmitter<{ email: string; password: string }>();

  onNext(): void {
    this.suivant.emit({
      email: (this.email || '').trim(),
      password: this.password
    });
  }
}
