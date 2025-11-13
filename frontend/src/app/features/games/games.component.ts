import { Component, Input, inject, signal, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { TPipe } from '@core/i18n';
import { GamesApiService } from '@core/http';
import { GameDto } from '@core/models';
import { GameCreateComponent } from './components/game-create.component';
import { GamePlayComponent } from './components/game-play.component';
import { GameResultsComponent } from './components/game-results.component';
import { GameDetailedResultsComponent } from './components/game-detailed-results.component';
import { GameSummaryComponent } from './components/game-summary.component';
import { interval, Subscription } from 'rxjs';

type GameView = 'none' | 'create' | 'play' | 'results' | 'detailed-results' | 'summary';

@Component({
  selector: 'app-games',
  standalone: true,
  imports: [
    CommonModule,
    TPipe,
    GameCreateComponent,
    GamePlayComponent,
    GameResultsComponent,
    GameDetailedResultsComponent,
    GameSummaryComponent
  ],
  template: `
    <div class="games-container">
      @if (loading()) {
        <div class="loading-state">
          <div class="spinner"></div>
          <p>{{ 'GAMES.LOADING' | t }}</p>
        </div>
      } @else if (error()) {
        <div class="alert alert-danger">
          {{ error() }}
        </div>
      } @else {
        <!-- No active game - Show create button for organizer -->
        @if (currentView() === 'none') {
          <div class="no-game-state">
            <div class="empty-state-icon">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
                <circle cx="12" cy="17" r=".5"/>
              </svg>
            </div>
            @if (isOrganizer) {
              <h3>{{ 'GAMES.NO_GAME.ORGANIZER_TITLE' | t }}</h3>
              <p>{{ 'GAMES.NO_GAME.ORGANIZER_MESSAGE' | t }}</p>
              <button class="btn btn-primary btn-lg" (click)="showCreateForm()">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M12 8v8m-4-4h8"/>
                </svg>
                {{ 'GAMES.NO_GAME.CREATE_GAME' | t }}
              </button>
            } @else {
              <h3>{{ 'GAMES.NO_GAME.PARTICIPANT_TITLE' | t }}</h3>
              <p>{{ 'GAMES.NO_GAME.PARTICIPANT_MESSAGE' | t }}</p>
            }
          </div>
        }

        <!-- Create game form -->
        @if (currentView() === 'create' && eventId) {
          <div class="game-create-view">
            <div class="view-header">
              <button class="btn btn-link" (click)="cancelCreate()">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M19 12H5m7-7l-7 7 7 7"/>
                </svg>
                {{ 'GAMES.BACK' | t }}
              </button>
            </div>
            <app-game-create
              [eventId]="eventId"
              (gameCreated)="onGameCreated($event)"
            />
          </div>
        }

        <!-- Active game - Play view -->
        @if (currentView() === 'play' && activeGame()) {
          <app-game-play
            [gameId]="activeGame()!.id"
            (gameCompleted)="onGameCompleted()"
          />
        }

        <!-- Detailed Results - Pagination through questions -->
        @if (currentView() === 'detailed-results' && completedGame()) {
          <app-game-detailed-results
            [gameId]="completedGame()!.id"
            (showSummary)="onShowSummary()"
          />
        }

        <!-- Summary - Final score and badges -->
        @if (currentView() === 'summary' && completedGame()) {
          <app-game-summary [gameId]="completedGame()!.id" />
          @if (isOrganizer) {
            <div class="summary-actions">
              <button class="btn btn-primary btn-lg" (click)="startNewGame()">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M12 8v8m-4-4h8"/>
                </svg>
                {{ 'GAMES.RESULTS.START_NEW_GAME' | t }}
              </button>
            </div>
          }
        }

        <!-- OLD Completed game - Results view (legacy) -->
        @if (currentView() === 'results' && completedGame()) {
          <div class="game-results-view">
            <app-game-results [gameId]="completedGame()!.id" />

            @if (isOrganizer) {
              <div class="results-actions">
                <button class="btn btn-primary btn-lg" (click)="startNewGame()">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <path d="M12 8v8m-4-4h8"/>
                  </svg>
                  {{ 'GAMES.RESULTS.START_NEW_GAME' | t }}
                </button>
              </div>
            }
          </div>
        }

        <!-- Game history section (collapsed by default) -->
        @if (gameHistory().length > 0 && currentView() !== 'results') {
          <div class="game-history-section">
            <button
              class="history-toggle"
              (click)="toggleHistory()"
            >
              <span>{{ 'GAMES.HISTORY.TITLE' | t }} ({{ gameHistory().length }})</span>
              <svg
                class="chevron"
                [class.open]="showHistory()"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M6 9l6 6 6-6"/>
              </svg>
            </button>

            @if (showHistory()) {
              <div class="history-list">
                @for (game of gameHistory(); track game.id) {
                  <div class="history-item" (click)="viewGameResults(game.id)">
                    <div class="history-info">
                      <span class="history-type">{{ 'GAMES.TYPES.' + game.game_type.toUpperCase() | t }}</span>
                      <span class="history-difficulty">{{ 'GAMES.DIFFICULTY.' + game.difficulty.toUpperCase() | t }}</span>
                      @if (game.status === 'COMPLETED') {
                        <span class="history-result" [class.correct]="game.is_correct">
                          {{ game.is_correct ? ('GAMES.HISTORY.SUCCESS' | t) : ('GAMES.HISTORY.FAILURE' | t) }}
                        </span>
                      }
                    </div>
                    <div class="history-meta">
                      <span class="history-date">{{ formatDate(game.created_at) }}</span>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M9 18l6-6-6-6"/>
                      </svg>
                    </div>
                  </div>
                }
              </div>
            }
          </div>
        }
      }
    </div>
  `,
  styles: [`
    .games-container {
      width: 100%;
    }

    .loading-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 60px 20px;
      color: #666;
    }

    .spinner {
      width: 48px;
      height: 48px;
      border: 4px solid #e0e0e0;
      border-top-color: #007bff;
      border-radius: 50%;
      animation: spin 1s linear infinite;
      margin-bottom: 16px;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    .alert {
      padding: 16px;
      border-radius: 4px;
      margin-bottom: 16px;
    }

    .alert-danger {
      background-color: #f8d7da;
      color: #721c24;
      border: 1px solid #f5c6cb;
    }

    .no-game-state {
      text-align: center;
      padding: 60px 20px;
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }

    .empty-state-icon {
      color: #9e9e9e;
      margin-bottom: 24px;
    }

    .no-game-state h3 {
      margin: 0 0 12px 0;
      font-size: 24px;
      color: #333;
    }

    .no-game-state p {
      margin: 0 0 32px 0;
      font-size: 16px;
      color: #666;
      max-width: 500px;
      margin-left: auto;
      margin-right: auto;
    }

    .btn {
      padding: 12px 24px;
      border: none;
      border-radius: 4px;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }

    .btn-primary {
      background-color: #007bff;
      color: white;
    }

    .btn-primary:hover {
      background-color: #0056b3;
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0,123,255,0.3);
    }

    .btn-lg {
      padding: 16px 32px;
      font-size: 18px;
    }

    .btn-link {
      background: none;
      color: #007bff;
      padding: 8px 0;
    }

    .btn-link:hover {
      color: #0056b3;
      text-decoration: underline;
    }

    .game-create-view, .game-results-view {
      animation: fadeIn 0.3s ease-in;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .view-header {
      margin-bottom: 16px;
    }

    .results-actions {
      margin-top: 32px;
      padding-top: 32px;
      border-top: 2px solid #e0e0e0;
      text-align: center;
    }

    .game-history-section {
      margin-top: 32px;
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      overflow: hidden;
    }

    .history-toggle {
      width: 100%;
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px 20px;
      background: none;
      border: none;
      cursor: pointer;
      font-size: 16px;
      font-weight: 600;
      color: #333;
      transition: background-color 0.2s;
    }

    .history-toggle:hover {
      background-color: #f5f5f5;
    }

    .chevron {
      transition: transform 0.3s ease;
    }

    .chevron.open {
      transform: rotate(180deg);
    }

    .history-list {
      border-top: 1px solid #e0e0e0;
    }

    .history-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px 20px;
      border-bottom: 1px solid #f0f0f0;
      cursor: pointer;
      transition: background-color 0.2s;
    }

    .history-item:hover {
      background-color: #fafafa;
    }

    .history-item:last-child {
      border-bottom: none;
    }

    .history-info {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }

    .history-type, .history-difficulty, .history-result {
      padding: 4px 10px;
      border-radius: 12px;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
    }

    .history-type {
      background-color: #e3f2fd;
      color: #1976d2;
    }

    .history-difficulty {
      background-color: #f3e5f5;
      color: #7b1fa2;
    }

    .history-result {
      background-color: #e0e0e0;
      color: #616161;
    }

    .history-result.correct {
      background-color: #e8f5e9;
      color: #2e7d32;
    }

    .history-meta {
      display: flex;
      align-items: center;
      gap: 8px;
      color: #999;
    }

    .history-date {
      font-size: 13px;
    }

    @media (max-width: 768px) {
      .no-game-state {
        padding: 40px 16px;
      }

      .history-item {
        flex-direction: column;
        align-items: flex-start;
        gap: 12px;
      }

      .history-meta svg {
        display: none;
      }
    }
  `]
})
export class GamesComponent implements OnInit, OnDestroy {
  @Input() eventId?: number;
  @Input() isOrganizer = false;

  private gamesApi = inject(GamesApiService);
  private route = inject(ActivatedRoute);

  currentView = signal<GameView>('none');
  loading = signal(true);
  error = signal<string | null>(null);
  activeGame = signal<GameDto | null>(null);
  completedGame = signal<GameDto | null>(null);
  gameHistory = signal<GameDto[]>([]);
  showHistory = signal(false);

  private pollingSubscription?: Subscription;
  private gamePublicId?: string;

  ngOnInit() {
    // Check if we're in standalone mode (route-based) or embedded mode (Input-based)
    const routeGameId = this.route.snapshot.paramMap.get('id');

    if (routeGameId) {
      // Standalone mode: load game by public_id
      this.gamePublicId = routeGameId;
      this.loadGameByPublicId(routeGameId);
    } else if (this.eventId) {
      // Embedded mode: load games for event
      this.loadGames();
    } else {
      this.error.set('No game or event ID provided');
      this.loading.set(false);
    }
  }

  ngOnDestroy() {
    this.stopPolling();
  }

  loadGames() {
    this.loading.set(true);
    this.error.set(null);

    if (!this.eventId) {
      this.error.set('No event ID provided');
      this.loading.set(false);
      return;
    }

    // Check if we're already viewing results/summary - don't try to load active game
    const currentView = this.currentView();
    if (currentView === 'detailed-results' || currentView === 'summary' || currentView === 'results') {
      this.loading.set(false);
      return;
    }

    // First try to get the active game for this event
    this.gamesApi.getActiveGame(this.eventId).subscribe({
      next: (activeGame) => {
        if (activeGame) {
          this.activeGame.set(activeGame);
          this.currentView.set('play');
          this.startPolling();
        } else {
          this.activeGame.set(null);
          this.currentView.set('none');
        }
        this.loading.set(false);
      },
      error: (err) => {
        // No active game found (404 is expected if no active game)
        if (err.status === 404) {
          this.activeGame.set(null);
          this.currentView.set('none');
          this.loading.set(false);
        } else {
          this.loading.set(false);
          this.error.set(err.error?.detail || err.message || 'Failed to load games');
        }
      }
    });
  }

  loadGameByPublicId(publicId: string) {
    this.loading.set(true);
    this.error.set(null);

    // In standalone mode, we need to get the game by its numeric ID
    // Since the API expects numeric IDs, we'll need to parse the public_id
    // or use a different endpoint. For now, let's try to load it directly.

    // The public_id is a UUID string, but the API get() method expects a number
    // We need to handle this differently - possibly via the list endpoint
    // or by adding a new backend endpoint that accepts public_id

    // For now, let's assume we can extract event info from the game itself
    // This is a limitation - ideally we'd have a backend endpoint: /games/by-public-id/:public_id

    // Temporary workaround: Try to parse as number (for testing)
    const numericId = parseInt(publicId, 10);
    if (!isNaN(numericId)) {
      this.gamesApi.get(numericId).subscribe({
        next: (game) => {
          this.activeGame.set(game);
          this.eventId = game.event_id;

          if (game.status === 'ACTIVE') {
            this.currentView.set('play');
            this.startPolling();
          } else if (game.status === 'COMPLETED') {
            this.completedGame.set(game);
            this.activeGame.set(null);
            this.currentView.set('detailed-results');
          }

          this.loading.set(false);
        },
        error: (err) => {
          this.loading.set(false);
          this.error.set(err.error?.detail || err.message || 'Failed to load game');
        }
      });
    } else {
      // public_id is a UUID, we need a different approach
      this.loading.set(false);
      this.error.set('Invalid game ID format. Please use the event page to access games.');
    }
  }

  startPolling() {
    // Poll for game updates every 5 seconds when viewing active game
    this.pollingSubscription = interval(5000).subscribe(() => {
      if (this.activeGame()) {
        this.gamesApi.get(this.activeGame()!.id).subscribe({
          next: (game) => {
            // Keep latest snapshot of the active game
            this.activeGame.set(game);
            // Treat only terminal states as completion
            if (game.status === 'COMPLETED') {
              this.stopPolling();
              this.onGameCompleted();
            }
          },
          error: (err) => {
            console.error('Failed to poll game status:', err);
          }
        });
      }
    });
  }

  stopPolling() {
    if (this.pollingSubscription) {
      this.pollingSubscription.unsubscribe();
      this.pollingSubscription = undefined;
    }
  }

  showCreateForm() {
    this.currentView.set('create');
  }

  cancelCreate() {
    this.currentView.set('none');
  }

  onGameCreated(gameId: number) {
    // Reload games to show the newly created active game
    this.loadGames();
  }

  onGameCompleted() {
    this.stopPolling();

    // Load the completed game and show detailed results
    if (this.activeGame()) {
      const completedId = this.activeGame()!.id;
      this.gamesApi.get(completedId).subscribe({
        next: (game) => {
          this.completedGame.set(game);
          this.activeGame.set(null);
          // Show detailed results with pagination instead of old results
          this.currentView.set('detailed-results');

          // Refresh game history
          this.loadGames();
        },
        error: (err) => {
          console.error('Failed to load completed game:', err);
          this.loadGames();
        }
      });
    }
  }

  onShowSummary() {
    this.currentView.set('summary');
  }

  startNewGame() {
    this.completedGame.set(null);
    this.currentView.set('create');
  }

  viewGameResults(gameId: number) {
    this.gamesApi.get(gameId).subscribe({
      next: (game) => {
        this.completedGame.set(game);
        this.currentView.set('results');
      },
      error: (err) => {
        this.error.set(err.error?.detail || err.message || 'Failed to load game');
      }
    });
  }

  toggleHistory() {
    this.showHistory.set(!this.showHistory());
  }

  formatDate(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) {
      return `${diffMins}m ago`;
    } else if (diffHours < 24) {
      return `${diffHours}h ago`;
    } else if (diffDays < 7) {
      return `${diffDays}d ago`;
    } else {
      return date.toLocaleDateString();
    }
  }
}
