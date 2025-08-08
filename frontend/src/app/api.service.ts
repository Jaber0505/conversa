import { Injectable, inject } from "@angular/core";
import { HttpClient } from "@angular/common/http";

@Injectable({ providedIn: "root" })
export class ApiService {
  private http = inject(HttpClient);
  private baseUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

  ping() {
    return this.http.get<{status: string}>(`${this.baseUrl}/api/ping/`);
  }
}
