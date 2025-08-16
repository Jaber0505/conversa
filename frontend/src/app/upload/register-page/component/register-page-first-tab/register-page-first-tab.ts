import {Component, EventEmitter, Output} from '@angular/core';
import {FirstTabInfoModel} from "@app/upload/register-page/models/firstTabInfo.model";
import {FormsModule} from "@angular/forms";
import {JsonPipe, NgIf} from "@angular/common";

@Component({
  selector: 'app-register-page-first-tab',
  imports: [FormsModule, JsonPipe, NgIf],
  templateUrl: './register-page-first-tab.html',
  standalone: true,
  styleUrl: './register-page-first-tab.scss'
})
export class RegisterPageFirstTab {
  firstTabInfo: FirstTabInfoModel = {} as FirstTabInfoModel;
  @Output() suivant = new EventEmitter<FirstTabInfoModel>();

  onNext(): void {
    this.suivant.emit(this.firstTabInfo);
  }
}
