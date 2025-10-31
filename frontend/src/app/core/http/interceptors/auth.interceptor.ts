// core/http/interceptors/auth.interceptor.ts
import {
  HttpInterceptorFn,
  HttpErrorResponse,
  HttpClient,
  HttpEvent,
  HttpRequest,
} from '@angular/common/http';
import { inject } from '@angular/core';
import { Observable, throwError, of } from 'rxjs';
import { catchError, map, switchMap, finalize, shareReplay, tap } from 'rxjs/operators';
import { AuthTokenService, API_URL } from '@core/http';
import { ErrorLoggerService } from '@app/core/services';

type RefreshResponse = { access: string; refresh?: string };

const isAuthEndpoint = (url: string) => /\/auth\/(login|register)\/?$/.test(url);
const isRefreshEndpoint = (url: string) => /\/auth\/refresh\/?$/.test(url);

// Gate partagé pour éviter plusieurs refresh simultanés
let refreshInFlight$: Observable<string> | null = null;

const doRefresh = (http: HttpClient, tokens: AuthTokenService, baseUrl: string): Observable<string> => {
  const refresh = tokens.refresh;
  if (!refresh) return throwError(() => new Error('No refresh token'));

  if (!refreshInFlight$) {
    refreshInFlight$ = http
      .post<RefreshResponse>(`${baseUrl}/auth/refresh/`, { refresh })
      .pipe(
        map((resp) => {
          tokens.save(resp.access, resp.refresh ?? null);
          return resp.access;
        }),
        finalize(() => {
          refreshInFlight$ = null;
        }),
        shareReplay(1)
      );
  }
  return refreshInFlight$;
};

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const tokens = inject(AuthTokenService);
  const http = inject(HttpClient);
  const apiBase = inject(API_URL);
  const errorLogger = inject(ErrorLoggerService);

  const hasAccess = !!tokens.access;
  const shouldAttach =
    hasAccess && !isAuthEndpoint(req.url) && !isRefreshEndpoint(req.url);

  const withAuth: HttpRequest<unknown> = shouldAttach
    ? req.clone({ setHeaders: { Authorization: `Bearer ${tokens.access!}` } })
    : req;

  return next(withAuth).pipe(
    catchError((err: unknown) => {
      // Log all HTTP errors
      if (err instanceof HttpErrorResponse) {
        errorLogger.logHttpError(err, {
          endpoint: req.url,
          method: req.method,
          hasAuth: shouldAttach,
        });
      }

      // Pas un HttpErrorResponse ou pas 401 → remonter l'erreur
      if (!(err instanceof HttpErrorResponse) || err.status !== 401) {
        return throwError(() => err);
      }
      // Ne jamais tenter de refresh sur login/register/refresh
      if (isAuthEndpoint(req.url) || isRefreshEndpoint(req.url)) {
        return throwError(() => err);
      }
      // Pas de refresh disponible → purge + remonter
      if (!tokens.refresh) {
        tokens.clear();
        return throwError(() => err);
      }

      // Refresh + rejouer la requête avec le nouvel access
      return doRefresh(http, tokens, apiBase).pipe(
        switchMap((newAccess) => {
          errorLogger.logInfo('Token refreshed successfully', { endpoint: req.url });
          const replay = req.clone({
            setHeaders: { Authorization: `Bearer ${newAccess}` },
          });
          return next(replay);
        }),
        catchError((e) => {
          tokens.clear();
          errorLogger.logError('Token refresh failed, clearing tokens', {
            endpoint: req.url,
            error: e,
          });
          return throwError(() => e);
        })
      );
    })
  );
};
