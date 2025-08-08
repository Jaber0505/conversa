import "zone.js";
import { bootstrapApplication } from "@angular/platform-browser";
import { provideHttpClient } from "@angular/common/http";
import { provideRouter, Routes, withEnabledBlockingInitialNavigation } from "@angular/router";
import { AppComponent } from "./app/app.component";
import { HomeComponent } from "./app/home.component";
import { NotFoundComponent } from "./app/not-found.component";

const routes: Routes = [
  { path: "", component: HomeComponent },
  { path: "**", component: NotFoundComponent },
];

bootstrapApplication(AppComponent, {
  providers: [
    provideRouter(routes, withEnabledBlockingInitialNavigation()),
    provideHttpClient(),
  ],
}).catch(err => console.error(err));
