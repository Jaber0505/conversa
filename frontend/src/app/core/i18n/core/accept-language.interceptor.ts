import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { LangService } from '@core/i18n';

export const acceptLanguageInterceptor: HttpInterceptorFn = (req, next) => {
  const lang = inject(LangService).current;
  return next(req.clone({ setHeaders: { 'Accept-Language': lang } }));
};
