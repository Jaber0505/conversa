import { Component, Input, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TPipe } from '@core/i18n';
import { GamesApiService } from '@core/http';
import { GameDto } from '@core/models';

@Component({
  selector: 'app-game-results',
  standalone: true,
  imports: [CommonModule, TPipe],
  template: `
    <div class="game-results-container">
      @if (loading()) {
        <div class="loading">
          <p>{{ 'GAMES.RESULTS.LOADING' | t }}</p>
        </div>
      } @else if (error()) {
        <div class="alert alert-danger">
          {{ 'GAMES.RESULTS.ERROR' | t }}: {{ error() }}
        </div>
      } @else if (game()) {
        <div class="results-card">
          <!-- Header -->
          <div class="results-header">
            <h3>{{ 'GAMES.RESULTS.TITLE' | t }}</h3>
            <div class="game-meta">
              <span class="game-type">{{ 'GAMES.TYPES.' + game()!.game_type.toUpperCase() | t }}</span>
              <span class="difficulty">{{ 'GAMES.DIFFICULTY.' + game()!.difficulty.toUpperCase() | t }}</span>
              <span class="status" [class]="'status-' + game()!.status.toLowerCase()">
                {{ 'GAMES.STATUS.' + game()!.status | t }}
              </span>
            </div>
          </div>

          <!-- Question -->
          <div class="question-section">
            @if (game()!.image_url) {
              <div class="question-image">
                <img [src]="game()!.image_url" [alt]="'GAMES.RESULTS.IMAGE_ALT' | t" />
              </div>
            }
            <p class="question-text">{{ game()!.question_text }}</p>
          </div>

          <!-- Result Summary -->
          <div class="result-summary">
            @if (game()!.status === 'COMPLETED') {
              <div class="result-box" [class.correct]="game()!.is_correct" [class.incorrect]="game()!.is_correct === false">
                <div class="result-icon">
                  @if (game()!.is_correct) {
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                    </svg>
                  } @else {
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                    </svg>
                  }
                </div>
                <h4>
                  @if (game()!.is_correct) {
                    {{ 'GAMES.RESULTS.SUCCESS_TITLE' | t }}
                  } @else {
                    {{ 'GAMES.RESULTS.FAILURE_TITLE' | t }}
                  }
                </h4>
                <p class="result-answer">
                  <strong>{{ 'GAMES.RESULTS.YOUR_ANSWER' | t }}:</strong> {{ game()!.final_answer }}
                </p>
                <p class="correct-answer">
                  <strong>{{ 'GAMES.RESULTS.CORRECT_ANSWER' | t }}:</strong> {{ game()!.correct_answer }}
                </p>
              </div>
            }
          </div>

          <!-- Voting Statistics -->
          <div class="stats-section">
            <h4>{{ 'GAMES.RESULTS.STATISTICS' | t }}</h4>

            <div class="stats-grid">
              <div class="stat-card">
                <span class="stat-label">{{ 'GAMES.RESULTS.TOTAL_PARTICIPANTS' | t }}</span>
                <span class="stat-value">{{ game()!.stats.confirmed_participants }}</span>
              </div>
              <div class="stat-card">
                <span class="stat-label">{{ 'GAMES.RESULTS.TOTAL_VOTES' | t }}</span>
                <span class="stat-value">{{ game()!.stats.total_votes }}</span>
              </div>
              <div class="stat-card">
                <span class="stat-label">{{ 'GAMES.RESULTS.PARTICIPATION_RATE' | t }}</span>
                <span class="stat-value">{{ getParticipationRate() }}%</span>
              </div>
            </div>

            @if (game()!.stats.vote_counts && Object.keys(game()!.stats.vote_counts).length > 0) {
              <div class="vote-breakdown">
                <h5>{{ 'GAMES.RESULTS.VOTE_BREAKDOWN' | t }}</h5>
                @for (entry of getVoteCountEntries(); track entry[0]) {
                  <div class="vote-row">
                    <div class="vote-answer-cell">
                      <span class="vote-answer">{{ entry[0] }}</span>
                      @if (entry[0] === game()!.correct_answer) {
                        <span class="correct-badge">{{ 'GAMES.RESULTS.CORRECT' | t }}</span>
                      }
                      @if (entry[0] === game()!.final_answer && game()!.status === 'COMPLETED') {
                        <span class="winner-badge">{{ 'GAMES.RESULTS.WINNER' | t }}</span>
                      }
                    </div>
                    <div class="vote-bar-cell">
                      <div class="vote-bar-wrapper">
                        <div
                          class="vote-bar"
                          [class.correct-bar]="entry[0] === game()!.correct_answer"
                          [class.winner-bar]="entry[0] === game()!.final_answer"
                          [style.width.%]="(entry[1] / game()!.stats.total_votes) * 100"
                        ></div>
                        <span class="vote-count">{{ entry[1] }} {{ 'GAMES.RESULTS.VOTES' | t }}</span>
                      </div>
                      <span class="vote-percentage">{{ ((entry[1] / game()!.stats.total_votes) * 100).toFixed(1) }}%</span>
                    </div>
                  </div>
                }
              </div>
            }
          </div>

          <!-- Individual Votes -->
          @if (game()!.votes && game()!.votes.length > 0) {
            <div class="votes-section">
              <h4>{{ 'GAMES.RESULTS.INDIVIDUAL_VOTES' | t }}</h4>
              <div class="votes-list">
                @for (vote of game()!.votes; track vote.id) {
                  <div class="vote-item">
                    <div class="vote-user">
                      <div class="user-avatar">
                        {{ getInitials(vote.user_email) }}
                      </div>
                      <span class="user-email">{{ vote.user_email }}</span>
                    </div>
                    <div class="vote-answer-box">
                      <span class="vote-answer-text">{{ vote.answer }}</span>
                      @if (vote.answer === game()!.correct_answer) {
                        <svg class="vote-check" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                        </svg>
                      }
                    </div>
                  </div>
                }
              </div>
            </div>
          }
        </div>
      }
    </div>
  `,
  styles: [`
    .game-results-container {
      max-width: 900px;
      margin: 0 auto;
    }

    .loading {
      text-align: center;
      padding: 40px;
      color: #666;
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

    .results-card {
      background: white;
      border-radius: 8px;
      padding: 24px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }

    .results-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
      padding-bottom: 16px;
      border-bottom: 2px solid #e0e0e0;
    }

    .results-header h3 {
      margin: 0;
      color: #333;
      font-size: 24px;
    }

    .game-meta {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }

    .game-type, .difficulty, .status {
      padding: 6px 14px;
      border-radius: 16px;
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .game-type {
      background-color: #e3f2fd;
      color: #1976d2;
    }

    .difficulty {
      background-color: #f3e5f5;
      color: #7b1fa2;
    }

    .status {
      background-color: #e0e0e0;
      color: #616161;
    }

    .status-completed {
      background-color: #e8f5e9;
      color: #2e7d32;
    }

    .question-section {
      margin-bottom: 32px;
    }

    .question-image {
      margin-bottom: 16px;
      text-align: center;
    }

    .question-image img {
      max-width: 100%;
      max-height: 400px;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }

    .question-text {
      font-size: 20px;
      font-weight: 600;
      color: #333;
      line-height: 1.5;
      margin: 0;
    }

    .result-summary {
      margin-bottom: 32px;
    }

    .result-box {
      text-align: center;
      padding: 40px;
      border-radius: 8px;
      background-color: #f5f5f5;
    }

    .result-box.correct {
      background-color: #e8f5e9;
      border: 2px solid #4caf50;
    }

    .result-box.incorrect {
      background-color: #ffebee;
      border: 2px solid #f44336;
    }

    .result-icon {
      margin-bottom: 16px;
    }

    .result-box.correct .result-icon {
      color: #4caf50;
    }

    .result-box.incorrect .result-icon {
      color: #f44336;
    }

    .result-box h4 {
      margin: 0 0 16px 0;
      font-size: 28px;
      color: #333;
    }

    .result-answer, .correct-answer {
      font-size: 16px;
      margin: 8px 0;
      color: #555;
    }

    .stats-section {
      margin-bottom: 32px;
    }

    .stats-section h4 {
      margin: 0 0 20px 0;
      color: #333;
      font-size: 20px;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 32px;
    }

    .stat-card {
      display: flex;
      flex-direction: column;
      padding: 20px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border-radius: 8px;
      color: white;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    .stat-label {
      font-size: 14px;
      opacity: 0.9;
      margin-bottom: 8px;
    }

    .stat-value {
      font-size: 32px;
      font-weight: 700;
    }

    .vote-breakdown h5 {
      margin: 0 0 16px 0;
      color: #555;
      font-size: 18px;
    }

    .vote-row {
      margin-bottom: 20px;
      padding: 16px;
      background-color: #fafafa;
      border-radius: 6px;
    }

    .vote-answer-cell {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
      flex-wrap: wrap;
    }

    .vote-answer {
      font-weight: 700;
      font-size: 16px;
      color: #333;
    }

    .correct-badge, .winner-badge {
      padding: 4px 10px;
      border-radius: 12px;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
    }

    .correct-badge {
      background-color: #4caf50;
      color: white;
    }

    .winner-badge {
      background-color: #2196f3;
      color: white;
    }

    .vote-bar-cell {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .vote-bar-wrapper {
      flex: 1;
      position: relative;
      height: 40px;
      background-color: #e0e0e0;
      border-radius: 6px;
      overflow: hidden;
    }

    .vote-bar {
      height: 100%;
      background: linear-gradient(90deg, #42a5f5, #1976d2);
      transition: width 0.5s ease;
      border-radius: 6px;
    }

    .vote-bar.correct-bar {
      background: linear-gradient(90deg, #66bb6a, #43a047);
    }

    .vote-bar.winner-bar {
      background: linear-gradient(90deg, #ffd54f, #ffb300);
    }

    .vote-count {
      position: absolute;
      left: 12px;
      top: 50%;
      transform: translateY(-50%);
      font-size: 14px;
      font-weight: 700;
      color: white;
      text-shadow: 0 1px 2px rgba(0,0,0,0.3);
    }

    .vote-percentage {
      min-width: 60px;
      text-align: right;
      font-weight: 700;
      color: #555;
    }

    .votes-section {
      padding-top: 32px;
      border-top: 2px solid #e0e0e0;
    }

    .votes-section h4 {
      margin: 0 0 20px 0;
      color: #333;
      font-size: 20px;
    }

    .votes-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .vote-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px;
      background-color: #fafafa;
      border-radius: 6px;
      border: 1px solid #e0e0e0;
    }

    .vote-user {
      display: flex;
      align-items: center;
      gap: 12px;
      flex: 1;
    }

    .user-avatar {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 14px;
      flex-shrink: 0;
    }

    .user-email {
      font-size: 14px;
      color: #555;
      word-break: break-word;
    }

    .vote-answer-box {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 16px;
      background-color: white;
      border-radius: 4px;
      border: 1px solid #ddd;
    }

    .vote-answer-text {
      font-weight: 600;
      color: #333;
    }

    .vote-check {
      color: #4caf50;
      flex-shrink: 0;
    }

    @media (max-width: 768px) {
      .results-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 12px;
      }

      .vote-item {
        flex-direction: column;
        align-items: flex-start;
        gap: 12px;
      }

      .vote-answer-box {
        width: 100%;
        justify-content: space-between;
      }
    }
  `]
})
export class GameResultsComponent implements OnInit {
  @Input() gameId!: number;

  private gamesApi = inject(GamesApiService);

  game = signal<GameDto | null>(null);
  loading = signal(true);
  error = signal<string | null>(null);

  Object = Object; // Expose Object to template

  ngOnInit() {
    this.loadGame();
  }

  loadGame() {
    this.loading.set(true);
    this.error.set(null);

    this.gamesApi.get(this.gameId).subscribe({
      next: (game) => {
        this.game.set(game);
        this.loading.set(false);
      },
      error: (err) => {
        this.loading.set(false);
        this.error.set(err.error?.detail || err.message || 'Failed to load game results');
      }
    });
  }

  getParticipationRate(): number {
    const currentGame = this.game();
    if (!currentGame || currentGame.stats.confirmed_participants === 0) {
      return 0;
    }
    return Math.round(
      (currentGame.stats.total_votes / currentGame.stats.confirmed_participants) * 100
    );
  }

  getVoteCountEntries(): [string, number][] {
    const voteCounts = this.game()?.stats.vote_counts || {};
    return Object.entries(voteCounts).sort((a, b) => b[1] - a[1]);
  }

  getInitials(email: string): string {
    if (!email) return '?';
    const parts = email.split('@')[0].split('.');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return email.substring(0, 2).toUpperCase();
  }
}
