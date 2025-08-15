import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { AuthTokenService } from '@core/http';
import { LangService } from '@core/i18n';

export const guestGuard: CanActivateFn = (_route, _state) => {
  const tokens = inject(AuthTokenService);
  if (!tokens.access) return true;

  const lang = inject(LangService).current;
  const router = inject(Router);
  return router.createUrlTree(['/', lang]);
};
