// core/api/base-api.service.ts
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { Problem } from '../models/problem.model';

@Injectable({ providedIn: 'root' })
export class BaseApiService {
  protected http = inject(HttpClient);
  protected baseUrl = environment.apiBaseUrl;

  protected get<T>(path: string, params?: any): Observable<T> {
    return this.http.get<T>(this.baseUrl + path, { params }).pipe(catchError(e => this.toProblem(e)));
  }

  protected post<TReq, TRes>(path: string, body: TReq): Observable<TRes> {
    return this.http.post<TRes>(this.baseUrl + path, body).pipe(catchError(e => this.toProblem(e)));
  }

  protected patch<TReq, TRes>(path: string, body: TReq): Observable<TRes> {
    return this.http.patch<TRes>(this.baseUrl + path, body).pipe(catchError(e => this.toProblem(e)));
  }

  protected del<TRes>(path: string): Observable<TRes> {
    return this.http.delete<TRes>(this.baseUrl + path).pipe(catchError(e => this.toProblem(e)));
  }

  private toProblem(err: HttpErrorResponse) {
    const p: Problem = err.error?.status ? err.error : {
      status: err.status || 0,
      code: err.status === 0 ? 'NETWORK_ERROR' : 'UNSPECIFIED_ERROR',
      detail: err.message || 'Request failed',
    };
    return throwError(() => p);
  }
}
