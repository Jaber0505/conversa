import { Component } from '@angular/core';
import {TPipe} from "@core/i18n";

@Component({
  selector: 'app-about',
  imports: [
    TPipe,
    TPipe
  ],
  templateUrl: './about.html',
  standalone: true,
  styleUrl: './about.scss'
})
export class About {

}
