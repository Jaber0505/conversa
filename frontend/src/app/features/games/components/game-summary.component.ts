import { Component, Input, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, ActivatedRoute } from '@angular/router';
import { TPipe } from '@core/i18n';
import { GamesApiService } from '@core/http';
import { GameResultDto } from '@core/models';

@Component({
  selector: 'app-game-summary',
  standalone: true,
  imports: [CommonModule, TPipe],
  template: `
    <div class="summary-container">
      @if (loading()) {
        <div class="loading">
          <p>{{ 'GAMES.SUMMARY.LOADING' | t }}</p>
        </div>
      } @else if (error()) {
        <div class="alert alert-danger">
          {{ 'GAMES.SUMMARY.ERROR' | t }}: {{ error() }}
        </div>
      } @else if (summary()) {
        <div class="summary-card">
          <!-- Badge Display -->
          <div class="badge-section" [class.victory]="summary()!.badge_type === 'victory'" [class.participation]="summary()!.badge_type === 'participation'">
            <div class="badge-icon">
              @if (summary()!.badge_type === 'victory') {
                <svg width="120" height="120" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"/>
                </svg>
              } @else {
                <svg width="120" height="120" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
              }
            </div>
            <h2>
              @if (summary()!.badge_type === 'victory') {
                {{ 'GAMES.SUMMARY.VICTORY' | t }}
              } @else {
                {{ 'GAMES.SUMMARY.PARTICIPATION' | t }}
              }
            </h2>
            <p class="badge-message">
              @if (summary()!.badge_type === 'victory') {
                {{ 'GAMES.SUMMARY.VICTORY_MESSAGE' | t }}
              } @else {
                {{ 'GAMES.SUMMARY.PARTICIPATION_MESSAGE' | t }}
              }
            </p>
          </div>

          <!-- Score Summary -->
          <div class="score-section">
            <h3>{{ 'GAMES.SUMMARY.SCORE_TITLE' | t }}</h3>
            <div class="score-display">
              <div class="score-circle" [style.--progress]="getScorePercentage()">
                <div class="score-value">
                  <span class="percentage">{{ getScorePercentage() }}%</span>
                  <span class="fraction">{{ summary()!.correct_answers }} / {{ summary()!.total_questions }}</span>
                </div>
              </div>
            </div>
            <p class="score-text">
              {{ 'GAMES.SUMMARY.CORRECT_ANSWERS' | t }}:
              <strong>{{ summary()!.correct_answers }}</strong> / {{ summary()!.total_questions }}
            </p>
          </div>

          <!-- Participants List -->
          @if (summary()!.badges && summary()!.badges.length > 0) {
            <div class="participants-section">
              <h3>{{ 'GAMES.SUMMARY.PARTICIPANTS' | t }} ({{ summary()!.badges.length }})</h3>
              <div class="participants-grid">
                @for (badge of summary()!.badges; track badge.id) {
                  <div class="participant-card">
                    <div class="participant-avatar">
                      {{ getInitials(badge.user_email) }}
                    </div>
                    <span class="participant-email">{{ badge.user_email }}</span>
                    <div class="participant-badge" [class.victory]="badge.badge_type === 'victory'">
                      @if (badge.badge_type === 'victory') {
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"/>
                        </svg>
                      } @else {
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                        </svg>
                      }
                    </div>
                  </div>
                }
              </div>
            </div>
          }

          <!-- Action Buttons -->
          <div class="action-buttons">
            <button class="btn btn-primary btn-lg" (click)="goToEvents()">
              {{ 'GAMES.SUMMARY.BACK_TO_EVENTS' | t }}
            </button>
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    .summary-container {
      max-width: 800px;
      margin: 0 auto;
      padding: 20px;
    }

    .loading {
      text-align: center;
      padding: 40px;
      color: #666;
    }

    .alert-danger {
      padding: 12px;
      border-radius: 4px;
      background-color: #f8d7da;
      color: #721c24;
      border: 1px solid #f5c6cb;
    }

    .summary-card {
      background: white;
      border-radius: 16px;
      padding: 40px;
      box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }

    .badge-section {
      text-align: center;
      padding: 40px 20px;
      border-radius: 12px;
      margin-bottom: 40px;
      animation: fadeInScale 0.6s ease-out;
    }

    .badge-section.victory {
      background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
      color: #333;
    }

    .badge-section.participation {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
    }

    @keyframes fadeInScale {
      from {
        opacity: 0;
        transform: scale(0.8);
      }
      to {
        opacity: 1;
        transform: scale(1);
      }
    }

    .badge-icon {
      animation: bounceIn 0.8s ease-out;
    }

    @keyframes bounceIn {
      0%, 20%, 50%, 80%, 100% {
        transform: translateY(0);
      }
      40% {
        transform: translateY(-20px);
      }
      60% {
        transform: translateY(-10px);
      }
    }

    .badge-section h2 {
      margin: 20px 0 16px;
      font-size: 36px;
      font-weight: 800;
    }

    .badge-message {
      font-size: 18px;
      margin: 0;
      opacity: 0.9;
    }

    .score-section {
      text-align: center;
      padding: 32px 20px;
      margin-bottom: 40px;
    }

    .score-section h3 {
      margin: 0 0 32px;
      font-size: 24px;
      color: #333;
    }

    .score-display {
      display: flex;
      justify-content: center;
      margin-bottom: 24px;
    }

    .score-circle {
      position: relative;
      width: 200px;
      height: 200px;
      border-radius: 50%;
      background: conic-gradient(
        #4caf50 0%,
        #4caf50 calc(var(--progress) * 1%),
        #e0e0e0 calc(var(--progress) * 1%),
        #e0e0e0 100%
      );
      display: flex;
      align-items: center;
      justify-content: center;
      animation: rotateIn 1s ease-out;
    }

    @keyframes rotateIn {
      from {
        transform: rotate(-180deg);
        opacity: 0;
      }
      to {
        transform: rotate(0deg);
        opacity: 1;
      }
    }

    .score-circle::before {
      content: '';
      position: absolute;
      width: 160px;
      height: 160px;
      border-radius: 50%;
      background: white;
    }

    .score-value {
      position: relative;
      display: flex;
      flex-direction: column;
      align-items: center;
    }

    .percentage {
      font-size: 48px;
      font-weight: 800;
      color: #4caf50;
    }

    .fraction {
      font-size: 18px;
      color: #666;
      margin-top: 4px;
    }

    .score-text {
      font-size: 18px;
      color: #666;
    }

    .participants-section {
      border-top: 2px solid #e0e0e0;
      padding-top: 32px;
    }

    .participants-section h3 {
      margin: 0 0 24px;
      font-size: 22px;
      color: #333;
    }

    .participants-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
      gap: 16px;
    }

    .participant-card {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 16px;
      background-color: #f8f9fa;
      border-radius: 8px;
      border: 2px solid #e0e0e0;
      transition: all 0.2s ease;
    }

    .participant-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    .participant-avatar {
      width: 48px;
      height: 48px;
      border-radius: 50%;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 18px;
      flex-shrink: 0;
    }

    .participant-email {
      flex: 1;
      font-size: 14px;
      color: #333;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .participant-badge {
      flex-shrink: 0;
      width: 32px;
      height: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 50%;
    }

    .participant-badge.victory {
      background-color: #ffd700;
      color: #333;
    }

    .participant-badge:not(.victory) {
      background-color: #667eea;
      color: white;
    }

    .action-buttons {
      margin-top: 40px;
      padding-top: 32px;
      border-top: 2px solid #e0e0e0;
      display: flex;
      justify-content: center;
    }

    .btn {
      padding: 16px 32px;
      border: none;
      border-radius: 12px;
      font-size: 18px;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.3s ease;
      text-decoration: none;
    }

    .btn-primary {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }

    .btn-primary:hover {
      transform: translateY(-3px);
      box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }

    .btn-primary:active {
      transform: translateY(-1px);
    }

    .btn-lg {
      font-size: 20px;
      padding: 18px 40px;
    }

    @media (max-width: 600px) {
      .summary-card {
        padding: 24px;
      }

      .badge-section h2 {
        font-size: 28px;
      }

      .score-circle {
        width: 160px;
        height: 160px;
      }

      .score-circle::before {
        width: 130px;
        height: 130px;
      }

      .percentage {
        font-size: 36px;
      }

      .participants-grid {
        grid-template-columns: 1fr;
      }
    }
  `]
})
export class GameSummaryComponent implements OnInit {
  @Input() gameId!: number;

  private gamesApi = inject(GamesApiService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);

  summary = signal<GameResultDto | null>(null);
  loading = signal(true);
  error = signal<string | null>(null);

  get lang(): string {
    return this.route.snapshot.paramMap.get('lang') ?? 'fr';
  }

  ngOnInit() {
    this.loadSummary();
  }

  loadSummary() {
    this.loading.set(true);
    this.error.set(null);

    this.gamesApi.getSummary(this.gameId).subscribe({
      next: (data) => {
        this.summary.set(data);
        this.loading.set(false);
      },
      error: (err) => {
        this.loading.set(false);
        this.error.set(err.error?.detail || err.message || 'Failed to load summary');
      }
    });
  }

  getScorePercentage(): number {
    const summaryData = this.summary();
    if (!summaryData) return 0;
    // Ensure score_percentage is a valid number
    const percentage = summaryData.score_percentage;
    if (percentage === null || percentage === undefined) return 0;
    // Convert to number and round to integer
    return Math.round(Number(percentage));
  }

  getInitials(email: string): string {
    if (!email) return '?';
    const parts = email.split('@')[0].split('.');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return email.substring(0, 2).toUpperCase();
  }

  goToEvents(): void {
    this.router.navigate(['/', this.lang, 'events']);
  }
}
