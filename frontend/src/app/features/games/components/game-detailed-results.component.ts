import { Component, Input, Output, EventEmitter, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TPipe } from '@core/i18n';
import { GamesApiService } from '@core/http';
import { DetailedResultsDto, QuestionResultDto } from '@core/models';

@Component({
  selector: 'app-game-detailed-results',
  standalone: true,
  imports: [CommonModule, TPipe],
  template: `
    <div class="detailed-results-container">
      @if (loading()) {
        <div class="loading">
          <p>{{ 'GAMES.DETAILED_RESULTS.LOADING' | t }}</p>
        </div>
      } @else if (error()) {
        <div class="alert alert-danger">
          {{ 'GAMES.DETAILED_RESULTS.ERROR' | t }}: {{ error() }}
        </div>
      } @else if (results() && currentQuestion()) {
        <div class="results-card">
          <!-- Header -->
          <div class="results-header">
            <h2>{{ 'GAMES.DETAILED_RESULTS.TITLE' | t }}</h2>
            <div class="progress-indicator">
              <span class="current">{{ currentQuestionIndex() + 1 }}</span> /
              <span class="total">{{ results()!.total_questions }}</span>
            </div>
          </div>

          <!-- Question Info -->
          <div class="question-info">
            <h3>{{ currentQuestion()!.question_text }}</h3>
            @if (currentQuestion()!.image_url) {
              <div class="question-image">
                <img [src]="currentQuestion()!.image_url" [alt]="'GAMES.DETAILED_RESULTS.IMAGE_ALT' | t" />
              </div>
            }
          </div>

          <!-- Team Result -->
          <div class="team-result" [class.correct]="currentQuestion()!.is_correct" [class.incorrect]="!currentQuestion()!.is_correct">
            <div class="result-icon">
              @if (currentQuestion()!.is_correct) {
                <svg width="64" height="64" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                </svg>
              } @else {
                <svg width="64" height="64" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                </svg>
              }
            </div>
            <h3>{{ currentQuestion()!.is_correct ? ('GAMES.DETAILED_RESULTS.CORRECT' | t) : ('GAMES.DETAILED_RESULTS.INCORRECT' | t) }}</h3>
            <div class="answer-summary">
              <p><strong>{{ 'GAMES.DETAILED_RESULTS.TEAM_ANSWER' | t }}:</strong> {{ currentQuestion()!.team_answer || ('GAMES.DETAILED_RESULTS.NO_ANSWER' | t) }}</p>
              <p><strong>{{ 'GAMES.DETAILED_RESULTS.CORRECT_ANSWER' | t }}:</strong> {{ currentQuestion()!.correct_answer }}</p>
            </div>
            @if (currentQuestion()!.context) {
              <div class="explanation">
                <p class="explanation-label">{{ 'GAMES.DETAILED_RESULTS.EXPLANATION' | t }}:</p>
                <p class="explanation-text">{{ currentQuestion()!.context }}</p>
              </div>
            }
          </div>

          <!-- Votes Details -->
          <div class="votes-section">
            <h4>{{ 'GAMES.DETAILED_RESULTS.VOTES_TITLE' | t }} ({{ currentQuestion()!.total_votes }})</h4>
            @if (currentQuestion()!.votes.length > 0) {
              <div class="votes-list">
                @for (vote of currentQuestion()!.votes; track vote.user_id) {
                  <div class="vote-item" [class.correct-vote]="vote.answer === currentQuestion()!.correct_answer">
                    <div class="user-info">
                      <svg class="user-icon" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                      </svg>
                      <span class="user-email">{{ vote.user_email }}</span>
                    </div>
                    <div class="vote-answer">
                      <span class="answer-badge">{{ vote.answer }}</span>
                      @if (vote.answer === currentQuestion()!.correct_answer) {
                        <svg class="check-icon" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                        </svg>
                      }
                    </div>
                  </div>
                }
              </div>
            } @else {
              <p class="no-votes">{{ 'GAMES.DETAILED_RESULTS.NO_VOTES' | t }}</p>
            }
          </div>

          <!-- Navigation -->
          <div class="navigation-buttons">
            @if (currentQuestionIndex() > 0) {
              <button class="btn btn-secondary" (click)="previousQuestion()">
                {{ 'GAMES.DETAILED_RESULTS.PREVIOUS' | t }}
              </button>
            }
            @if (currentQuestionIndex() < results()!.total_questions - 1) {
              <button class="btn btn-primary" (click)="nextQuestion()">
                {{ 'GAMES.DETAILED_RESULTS.NEXT_QUESTION' | t }}
              </button>
            } @else {
              <button class="btn btn-success" (click)="goToSummary()">
                {{ 'GAMES.DETAILED_RESULTS.VIEW_SUMMARY' | t }}
              </button>
            }
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    .detailed-results-container {
      max-width: 900px;
      margin: 0 auto;
      padding: 20px;
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
      border-radius: 12px;
      padding: 32px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    .results-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 32px;
      padding-bottom: 20px;
      border-bottom: 2px solid #e0e0e0;
    }

    .results-header h2 {
      margin: 0;
      color: #333;
      font-size: 28px;
    }

    .progress-indicator {
      font-size: 20px;
      font-weight: 600;
      color: #666;
    }

    .progress-indicator .current {
      color: #007bff;
      font-size: 24px;
    }

    .question-info {
      margin-bottom: 32px;
    }

    .question-info h3 {
      font-size: 22px;
      color: #333;
      margin-bottom: 16px;
      line-height: 1.5;
    }

    .question-image {
      text-align: center;
      margin: 20px 0;
    }

    .question-image img {
      max-width: 100%;
      max-height: 400px;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }

    .team-result {
      text-align: center;
      padding: 32px;
      border-radius: 12px;
      margin-bottom: 32px;
    }

    .team-result.correct {
      background-color: #e8f5e9;
      border: 3px solid #4caf50;
    }

    .team-result.incorrect {
      background-color: #ffebee;
      border: 3px solid #f44336;
    }

    .result-icon {
      margin-bottom: 16px;
    }

    .team-result.correct .result-icon {
      color: #4caf50;
    }

    .team-result.incorrect .result-icon {
      color: #f44336;
    }

    .team-result h3 {
      margin: 0 0 20px 0;
      font-size: 28px;
    }

    .team-result.correct h3 {
      color: #2e7d32;
    }

    .team-result.incorrect h3 {
      color: #c62828;
    }

    .answer-summary {
      margin: 20px 0;
    }

    .answer-summary p {
      margin: 12px 0;
      font-size: 18px;
      color: #333;
    }

    .explanation {
      margin-top: 24px;
      padding: 20px;
      background-color: rgba(255,255,255,0.7);
      border-radius: 8px;
      border-left: 4px solid #2196f3;
      text-align: left;
    }

    .explanation-label {
      font-weight: 700;
      font-size: 16px;
      margin: 0 0 8px 0 !important;
      color: #1976d2;
    }

    .explanation-text {
      margin: 0 !important;
      font-size: 15px;
      line-height: 1.6;
      color: #555;
      font-style: italic;
    }

    .votes-section {
      margin-bottom: 32px;
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
      background-color: #f5f5f5;
      border-radius: 8px;
      border-left: 4px solid #ccc;
      transition: all 0.2s ease;
    }

    .vote-item.correct-vote {
      background-color: #e8f5e9;
      border-left-color: #4caf50;
    }

    .user-info {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .user-icon {
      color: #666;
      flex-shrink: 0;
    }

    .user-email {
      font-weight: 500;
      color: #333;
    }

    .vote-answer {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .answer-badge {
      padding: 6px 16px;
      background-color: white;
      border: 2px solid #ddd;
      border-radius: 20px;
      font-weight: 600;
      color: #333;
    }

    .vote-item.correct-vote .answer-badge {
      border-color: #4caf50;
      background-color: #fff;
      color: #2e7d32;
    }

    .check-icon {
      color: #4caf50;
    }

    .no-votes {
      text-align: center;
      padding: 32px;
      color: #999;
      font-style: italic;
    }

    .navigation-buttons {
      display: flex;
      justify-content: space-between;
      gap: 16px;
      margin-top: 32px;
    }

    .btn {
      flex: 1;
      padding: 14px 32px;
      border: none;
      border-radius: 8px;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
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

    .btn-secondary {
      background-color: #6c757d;
      color: white;
    }

    .btn-secondary:hover {
      background-color: #545b62;
    }

    .btn-success {
      background-color: #28a745;
      color: white;
    }

    .btn-success:hover {
      background-color: #218838;
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(40,167,69,0.3);
    }

    @media (max-width: 600px) {
      .results-card {
        padding: 20px;
      }

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

      .navigation-buttons {
        flex-direction: column;
      }
    }
  `]
})
export class GameDetailedResultsComponent implements OnInit {
  @Input() gameId!: number;
  @Output() showSummary = new EventEmitter<void>();

  private gamesApi = inject(GamesApiService);

  results = signal<DetailedResultsDto | null>(null);
  currentQuestionIndex = signal(0);
  loading = signal(true);
  error = signal<string | null>(null);

  ngOnInit() {
    this.loadResults();
  }

  loadResults() {
    this.loading.set(true);
    this.error.set(null);

    this.gamesApi.getDetailedResults(this.gameId).subscribe({
      next: (data) => {
        this.results.set(data);
        this.loading.set(false);
      },
      error: (err) => {
        this.loading.set(false);
        this.error.set(err.error?.detail || err.message || 'Failed to load results');
      }
    });
  }

  currentQuestion(): QuestionResultDto | null {
    const r = this.results();
    if (!r || !r.questions || r.questions.length === 0) {
      return null;
    }
    return r.questions[this.currentQuestionIndex()];
  }

  nextQuestion() {
    const r = this.results();
    if (r && this.currentQuestionIndex() < r.total_questions - 1) {
      this.currentQuestionIndex.set(this.currentQuestionIndex() + 1);
    }
  }

  previousQuestion() {
    if (this.currentQuestionIndex() > 0) {
      this.currentQuestionIndex.set(this.currentQuestionIndex() - 1);
    }
  }

  goToSummary() {
    this.showSummary.emit();
  }
}
