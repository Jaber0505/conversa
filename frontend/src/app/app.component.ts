import { Component } from "@angular/core";
import { RouterLink, RouterOutlet } from "@angular/router";

@Component({
  selector: "app-root",
  standalone: true,
  imports: [RouterLink, RouterOutlet],
  template: `
    <header class="p-3">
      <a routerLink="/" class="brand">Conversa</a>
    </header>

    <main class="p-4">
      <router-outlet></router-outlet>
    </main>
  `,
  styles: [`
    .brand { font-weight: 600; text-decoration: none; }
    header { border-bottom: 1px solid #eee; }
  `]
})
export class AppComponent {}
