/**
 * Configuration globale de l'application (Angular standalone).
 * Fournit HttpClient (moderne) et le Router à partir des routes déclarées.
 * Point d’extension idéal pour ajouter interceptors/guards plus tard.
 */
import { ApplicationConfig } from '@angular/core';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideHttpClient(withInterceptorsFromDi()),
    provideRouter(routes),
  ],
};
