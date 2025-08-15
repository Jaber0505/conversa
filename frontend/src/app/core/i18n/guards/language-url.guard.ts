import { CanMatchFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { SUPPORTED_LANGS, DEFAULT_LANGUAGE, type Lang, LangService } from '@core/i18n';

export const languageUrlGuard: CanMatchFn = (_route, segments) => {
  const router = inject(Router);
  const langSvc = inject(LangService);

  const first = segments[0]?.path as Lang | undefined;
  if (!first) return router.createUrlTree(['/', DEFAULT_LANGUAGE]);

  const ok = (SUPPORTED_LANGS as readonly string[]).includes(first);
    if (!ok) return router.createUrlTree(['/', DEFAULT_LANGUAGE]);

    langSvc.set(first, { navigate: false });
    return true;
};
