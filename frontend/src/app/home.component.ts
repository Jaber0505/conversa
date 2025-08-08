import { Component, inject } from "@angular/core";
import { ApiService } from "./api.service";

@Component({
  standalone: true,
  selector: "app-home",
  template: `
    <h1>Accueil</h1>
    <button (click)="test()">Tester API</button>
    <pre *ngIf="out">{{ out | json }}</pre>
  `
})
export class HomeComponent {
  private api = inject(ApiService);
  out: unknown;

  test() {
    this.api.ping().subscribe({
      next: (res) => this.out = res,
      error: (err) => this.out = err,
    });
  }
}
