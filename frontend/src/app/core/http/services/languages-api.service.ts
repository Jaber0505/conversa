import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Language } from '@app/core/models/languages.model';
import { Paginated } from '@app/core/models/common.model';
import { API_URL } from '@core/http';

@Injectable({ providedIn: 'root' })
export class LanguagesApiService {
  private http = inject(HttpClient);
  private base = inject(API_URL);

  list() {
    return this.http.get<Paginated<Language>>(`${this.base}/languages/`);
  }

  get(id: number) {
    return this.http.get<Language>(`${this.base}/languages/${id}/`);
  }
}
