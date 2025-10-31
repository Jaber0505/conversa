// src/app/app.config.ts
import { ApplicationConfig, provideEnvironmentInitializer, inject, isDevMode } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors, withInterceptorsFromDi } from '@angular/common/http';

import { routes } from './app.routes';
import { acceptLanguageInterceptor, I18nService, LangService } from '@core/i18n';
import { authInterceptor } from '@core/http';

// Suppress Angular dev mode message
if (isDevMode()) {
  const originalWarn = console.warn;
  console.warn = (...args: any[]) => {
    if (args[0]?.includes?.('Angular is running in development mode')) return;
    originalWarn.apply(console, args);
  };
}

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    provideHttpClient(
      withInterceptors([acceptLanguageInterceptor, authInterceptor]),
      withInterceptorsFromDi()
    ),
    provideEnvironmentInitializer(() => {
      const i18n = inject(I18nService);
      const current = inject(LangService).current;
      void i18n.preload(current);
    }),
  ],
};
