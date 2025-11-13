import { Component, Input, Output, EventEmitter, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TPipe } from '@core/i18n';
import { GamesApiService } from '@core/http';
import { GameType } from '@core/models';

@Component({
  selector: 'app-game-create',
  standalone: true,
  imports: [CommonModule, FormsModule, TPipe],
  template: `
    <div class="game-create-card">
      <h3>{{ 'GAMES.CREATE.TITLE' | t }}</h3>

      @if (loading()) {
        <p>{{ 'GAMES.CREATE.LOADING' | t }}</p>
      } @else if (error()) {
        <div class="alert alert-danger">
          {{ 'GAMES.CREATE.ERROR' | t }}: {{ error() }}
        </div>
      } @else {
        <form (ngSubmit)="onCreate()" #gameForm="ngForm">
          <!-- Game Type Selection -->
          <div class="form-group">
            <label for="gameType">{{ 'GAMES.CREATE.TYPE' | t }}</label>
            <select
              id="gameType"
              class="form-control"
              [(ngModel)]="gameType"
              name="gameType"
              required
            >
              <option value="">{{ 'GAMES.CREATE.SELECT_TYPE' | t }}</option>
              <option value="picture_description">{{ 'GAMES.TYPES.PICTURE_DESCRIPTION' | t }}</option>
              <option value="word_association">{{ 'GAMES.TYPES.WORD_ASSOCIATION' | t }}</option>
            </select>
          </div>

          <div class="form-actions">
            <button
              type="submit"
              class="btn btn-primary"
              [disabled]="!gameForm.valid || loading()"
            >
              {{ 'GAMES.CREATE.START_GAME' | t }}
            </button>
          </div>
        </form>
      }
    </div>
  `,
  styles: [`
    .game-create-card {
      background: white;
      border-radius: 8px;
      padding: 24px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }

    h3 {
      margin-top: 0;
      margin-bottom: 24px;
      color: #333;
    }

    .form-group {
      margin-bottom: 20px;
    }

    label {
      display: block;
      margin-bottom: 8px;
      font-weight: 600;
      color: #555;
    }

    .form-control {
      width: 100%;
      padding: 10px 12px;
      border: 1px solid #ddd;
      border-radius: 4px;
      font-size: 14px;
    }

    .form-control:focus {
      outline: none;
      border-color: #007bff;
      box-shadow: 0 0 0 3px rgba(0,123,255,0.1);
    }

    .form-actions {
      margin-top: 24px;
    }

    .btn {
      padding: 12px 24px;
      border: none;
      border-radius: 4px;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      transition: background-color 0.2s;
    }

    .btn-primary {
      background-color: #007bff;
      color: white;
    }

    .btn-primary:hover:not(:disabled) {
      background-color: #0056b3;
    }

    .btn:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    .alert {
      padding: 12px;
      border-radius: 4px;
      margin-bottom: 16px;
    }

    .alert-danger {
      background-color: #f8d7da;
      color: #721c24;
      border: 1px solid #f5c6cb;
    }
  `]
})
export class GameCreateComponent {
  @Input() eventId!: number;
  @Output() gameCreated = new EventEmitter<number>();

  private gamesApi = inject(GamesApiService);

  gameType: GameType | '' = '';

  loading = signal(false);
  error = signal<string | null>(null);

  onCreate() {
    if (!this.gameType) {
      return;
    }

    this.loading.set(true);
    this.error.set(null);

    this.gamesApi.create({
      event_id: this.eventId,
      game_type: this.gameType as GameType
    }).subscribe({
      next: (game) => {
        this.loading.set(false);
        this.gameCreated.emit(game.id);
      },
      error: (err) => {
        this.loading.set(false);
        this.error.set(err.error?.detail || err.message || 'Failed to create game');
      }
    });
  }
}
