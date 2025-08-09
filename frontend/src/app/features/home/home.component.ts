import { Component } from '@angular/core';
import { ApiClientService } from '../../core/services/api-client.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss'],
})
export class HomeComponent {
  loading = false;
  status = '';
  message = '';
  error: string | null = null;

  constructor(private api: ApiClientService) {}

  tester() {
    this.loading = true;
    this.error = null;
    this.status = '';
    this.message = '';

    this.api.ping().subscribe({
      next: ({ status, message }) => {
        this.status = status;
        this.message = message;
        this.loading = false;
      },
      error: () => {
        this.error = 'Impossible de contacter le backend ❌';
        this.loading = false;
      }
    });
  }
}
