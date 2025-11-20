import { Component, Input, Output, EventEmitter, inject, signal, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TPipe } from '@core/i18n';
import { GamesApiService, AuthApiService } from '@core/http';
import { GameDto, GameStatsDto } from '@core/models';
import { interval, Subscription } from 'rxjs';
import { switchMap, takeWhile, take } from 'rxjs/operators';

@Component({
  selector: 'app-game-play',
  standalone: true,
  imports: [CommonModule, FormsModule, TPipe],
  template: `
    <div class="game-play-container">
      @if (loading()) {
        <div class="loading">
          <p>{{ 'GAMES.PLAY.LOADING' | t }}</p>
        </div>
      } @else if (error()) {
        <div class="alert alert-danger">
          {{ 'GAMES.PLAY.ERROR' | t }}: {{ error() }}
        </div>
      } @else if (game()) {
        <div class="game-card">
          <!-- Game Header -->
          <div class="game-header">
            <h3>{{ 'GAMES.PLAY.TITLE' | t }}</h3>
            <div class="game-meta">
              <span class="game-type">{{ 'GAMES.TYPES.' + game()!.game_type.toUpperCase() | t }}</span>
              <span class="difficulty">{{ 'GAMES.DIFFICULTY.' + game()!.difficulty.toUpperCase() | t }}</span>
              <span class="language-badge">
                {{ 'GAMES.PLAY.LANGUAGE_BADGE' | t }} {{ (game()!.language_code || '').toUpperCase() }}
              </span>
            </div>
          </div>

          <!-- Question Progress -->
          <div class="question-progress">
            <p>{{ 'GAMES.PLAY.QUESTION' | t }} {{ game()!.current_question_index + 1 }} / {{ game()!.total_questions }}</p>
          </div>

          <!-- Question -->
          <div class="question-section">
            @if (game()!.image_url) {
              <div class="question-image">
                <img [src]="game()!.image_url" [alt]="'GAMES.PLAY.IMAGE_ALT' | t" />
              </div>
            }
            <p class="question-text">{{ game()!.question_text }}</p>
          </div>

          <!-- Voting Section with Options -->
          @if (!hasVoted() && game()!.status === 'ACTIVE') {
            <div class="voting-section">
              <p class="vote-label">{{ 'GAMES.PLAY.SELECT_ANSWER' | t }}</p>
              <div class="options-grid">
                @for (option of game()!.options; track option) {
                  <button
                    class="option-button"
                    [class.selected]="selectedOption() === option"
                    (click)="selectOption(option)"
                    [disabled]="submitting()"
                  >
                    {{ option }}
                  </button>
                }
              </div>
              <button
                class="btn btn-primary submit-btn"
                (click)="onSubmitVote()"
                [disabled]="!selectedOption() || submitting()"
              >
                {{ submitting() ? ('GAMES.PLAY.SUBMITTING' | t) : ('GAMES.PLAY.SUBMIT_VOTE' | t) }}
              </button>
            </div>
          } @else if (hasVoted() && game()!.status === 'ACTIVE') {
            <div class="voted-message">
              <svg class="check-icon" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
              </svg>
              <p>{{ 'GAMES.PLAY.VOTE_SUBMITTED' | t }}</p>
              <p class="your-vote">{{ 'GAMES.PLAY.YOUR_VOTE' | t }}: <strong>{{ getUserVote() }}</strong></p>
            </div>
          }

          <!-- Statistics -->
          @if (stats()) {
            <div class="stats-section">
              <h4>{{ 'GAMES.PLAY.STATS_TITLE' | t }}</h4>
              <div class="stats-grid">
                <div class="stat-item">
                  <span class="stat-label">{{ 'GAMES.PLAY.TOTAL_VOTES' | t }}</span>
                  <span class="stat-value">{{ stats()!.total_votes }} / {{ stats()!.confirmed_participants }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">{{ 'GAMES.PLAY.VOTES_REMAINING' | t }}</span>
                  <span class="stat-value">{{ stats()!.votes_remaining }}</span>
                </div>
              </div>

              @if (stats()!.vote_counts && Object.keys(stats()!.vote_counts).length > 0) {
                <div class="vote-distribution">
                  <h5>{{ 'GAMES.PLAY.VOTE_DISTRIBUTION' | t }}</h5>
                  @for (entry of getVoteCountEntries(); track entry[0]) {
                    <div class="vote-bar-container">
                      <span class="vote-answer">{{ entry[0] }}</span>
                      <div class="vote-bar-wrapper">
                        <div
                          class="vote-bar"
                          [style.width.%]="(entry[1] / stats()!.total_votes) * 100"
                        ></div>
                        <span class="vote-count">{{ entry[1] }}</span>
                      </div>
                    </div>
                  }
                </div>
              }
            </div>
          }

          <!-- Organizer Controls -->
          @if (isOrganizer()) {
            <div class="organizer-controls">
              <h4>{{ 'GAMES.PLAY.ORGANIZER_CONTROLS' | t }}</h4>

              @if (game()!.status === 'ACTIVE') {
                <!-- Reveal Answer Button -->
                <button
                  class="btn btn-warning"
                  (click)="onRevealAnswer()"
                  [disabled]="revealing()"
                >
                  {{ revealing() ? ('GAMES.PLAY.REVEALING' | t) : ('GAMES.PLAY.REVEAL_ANSWER' | t) }}
                </button>
                <p class="control-hint">{{ 'GAMES.PLAY.REVEAL_HINT' | t }}</p>
              }

              @if (game()!.status === 'SHOWING_RESULTS') {
                <!-- Answer Result Display -->
                <div class="answer-result" [class.correct]="game()!.is_correct" [class.incorrect]="!game()!.is_correct">
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
                  <h3>{{ game()!.is_correct ? ('GAMES.PLAY.CORRECT' | t) : ('GAMES.PLAY.INCORRECT' | t) }}</h3>
                  <p><strong>{{ 'GAMES.PLAY.TEAM_ANSWER' | t }}:</strong> {{ game()!.final_answer || ('GAMES.PLAY.NO_VOTES' | t) }}</p>
                  <p><strong>{{ 'GAMES.PLAY.CORRECT_ANSWER' | t }}:</strong> {{ game()!.correct_answer }}</p>
                  @if (game()!.context) {
                    <div class="explanation">
                      <p class="explanation-label">{{ 'GAMES.PLAY.EXPLANATION' | t }}:</p>
                      <p class="explanation-text">{{ game()!.context }}</p>
                    </div>
                  }
                </div>

                <!-- Next Question Button -->
                <button
                  class="btn btn-primary"
                  (click)="onNextQuestion()"
                  [disabled]="movingNext()"
                >
                  {{ movingNext() ? ('GAMES.PLAY.MOVING_NEXT' | t) : ('GAMES.PLAY.NEXT_QUESTION' | t) }}
                </button>
                <p class="control-hint">{{ 'GAMES.PLAY.NEXT_HINT' | t }}</p>
              }
            </div>
          } @else {
            <!-- Participant waiting for organizer -->
            @if (game()!.status === 'SHOWING_RESULTS') {
              <div class="waiting-organizer">
                <div class="answer-result" [class.correct]="game()!.is_correct" [class.incorrect]="!game()!.is_correct">
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
                  <h3>{{ game()!.is_correct ? ('GAMES.PLAY.CORRECT' | t) : ('GAMES.PLAY.INCORRECT' | t) }}</h3>
                  <p><strong>{{ 'GAMES.PLAY.TEAM_ANSWER' | t }}:</strong> {{ game()!.final_answer || ('GAMES.PLAY.NO_VOTES' | t) }}</p>
                  <p><strong>{{ 'GAMES.PLAY.CORRECT_ANSWER' | t }}:</strong> {{ game()!.correct_answer }}</p>
                  @if (game()!.context) {
                    <div class="explanation">
                      <p class="explanation-label">{{ 'GAMES.PLAY.EXPLANATION' | t }}:</p>
                      <p class="explanation-text">{{ game()!.context }}</p>
                    </div>
                  }
                </div>
                <p class="waiting-message">{{ 'GAMES.PLAY.WAITING_ORGANIZER' | t }}</p>
              </div>
            }
          }
        </div>
      }
    </div>
  `,
  styles: [`
    .game-play-container {
      max-width: 800px;
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

    .game-card {
      background: white;
      border-radius: 8px;
      padding: 24px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }

    .game-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      padding-bottom: 16px;
      border-bottom: 1px solid #e0e0e0;
    }

    .game-header h3 {
      margin: 0;
      color: #333;
    }

    .game-meta {
      display: flex;
      gap: 12px;
    }

    .game-type, .difficulty, .language-badge {
      padding: 4px 12px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
    }

    .game-type {
      background-color: #e3f2fd;
      color: #1976d2;
    }

    .difficulty {
      background-color: #f3e5f5;
      color: #7b1fa2;
    }

    .language-badge {
      background-color: #fff3e0;
      color: #f57c00;
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

    .voting-section {
      margin-bottom: 32px;
    }

    .vote-label {
      display: block;
      margin-bottom: 16px;
      font-weight: 600;
      font-size: 18px;
      color: #333;
    }

    .options-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 12px;
      margin-bottom: 24px;
    }

    .option-button {
      padding: 16px 20px;
      border: 2px solid #ddd;
      border-radius: 8px;
      background-color: white;
      font-size: 16px;
      font-weight: 500;
      color: #333;
      cursor: pointer;
      transition: all 0.2s ease;
      text-align: center;
    }

    .option-button:hover:not(:disabled) {
      border-color: #007bff;
      background-color: #f0f8ff;
      transform: translateY(-2px);
      box-shadow: 0 4px 8px rgba(0,123,255,0.2);
    }

    .option-button.selected {
      border-color: #007bff;
      background-color: #007bff;
      color: white;
    }

    .option-button:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    .submit-btn {
      width: 100%;
      padding: 14px;
      font-size: 18px;
    }

    .form-control {
      width: 100%;
      padding: 12px;
      border: 2px solid #ddd;
      border-radius: 4px;
      font-size: 16px;
      margin-bottom: 12px;
      transition: border-color 0.2s;
    }

    .form-control:focus {
      outline: none;
      border-color: #007bff;
      box-shadow: 0 0 0 3px rgba(0,123,255,0.1);
    }

    .form-control:disabled {
      background-color: #f5f5f5;
      cursor: not-allowed;
    }

    .btn {
      padding: 12px 32px;
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

    .voted-message {
      text-align: center;
      padding: 32px;
      background-color: #e8f5e9;
      border-radius: 8px;
      margin-bottom: 32px;
    }

    .check-icon {
      color: #4caf50;
      margin-bottom: 12px;
    }

    .voted-message p {
      margin: 8px 0;
      color: #2e7d32;
      font-size: 16px;
    }

    .your-vote {
      font-size: 14px;
      color: #555;
    }

    .your-vote strong {
      color: #333;
    }

    .stats-section {
      padding-top: 24px;
      border-top: 1px solid #e0e0e0;
    }

    .stats-section h4 {
      margin: 0 0 16px 0;
      color: #333;
      font-size: 18px;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }

    .stat-item {
      display: flex;
      flex-direction: column;
      padding: 16px;
      background-color: #f5f5f5;
      border-radius: 4px;
    }

    .stat-label {
      font-size: 14px;
      color: #666;
      margin-bottom: 4px;
    }

    .stat-value {
      font-size: 24px;
      font-weight: 700;
      color: #333;
    }

    .vote-distribution h5 {
      margin: 0 0 16px 0;
      color: #555;
      font-size: 16px;
    }

    .vote-bar-container {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 12px;
    }

    .vote-answer {
      min-width: 120px;
      font-weight: 600;
      color: #333;
      word-break: break-word;
    }

    .vote-bar-wrapper {
      flex: 1;
      position: relative;
      height: 32px;
      background-color: #f5f5f5;
      border-radius: 4px;
      overflow: hidden;
    }

    .vote-bar {
      height: 100%;
      background: linear-gradient(90deg, #42a5f5, #1976d2);
      transition: width 0.3s ease;
      border-radius: 4px;
    }

    .vote-count {
      position: absolute;
      right: 8px;
      top: 50%;
      transform: translateY(-50%);
      font-size: 14px;
      font-weight: 600;
      color: #333;
    }

    .question-progress {
      text-align: center;
      padding: 8px 16px;
      background-color: #f0f0f0;
      border-radius: 4px;
      margin-bottom: 16px;
      font-weight: 600;
      color: #555;
    }

    .organizer-controls {
      margin-top: 32px;
      padding: 24px;
      background-color: #fff9e6;
      border: 2px solid #ffc107;
      border-radius: 8px;
    }

    .organizer-controls h4 {
      margin: 0 0 16px 0;
      color: #f57c00;
      font-size: 18px;
    }

    .btn-warning {
      background-color: #ffc107;
      color: #333;
    }

    .btn-warning:hover:not(:disabled) {
      background-color: #ffb300;
    }

    .control-hint {
      margin: 12px 0 0 0;
      font-size: 14px;
      color: #666;
      font-style: italic;
    }

    .answer-result {
      text-align: center;
      padding: 32px;
      border-radius: 8px;
      margin-bottom: 24px;
    }

    .answer-result.correct {
      background-color: #e8f5e9;
      border: 2px solid #4caf50;
    }

    .answer-result.incorrect {
      background-color: #ffebee;
      border: 2px solid #f44336;
    }

    .result-icon {
      margin-bottom: 16px;
    }

    .answer-result.correct .result-icon {
      color: #4caf50;
    }

    .answer-result.incorrect .result-icon {
      color: #f44336;
    }

    .answer-result h3 {
      margin: 0 0 16px 0;
      font-size: 24px;
    }

    .answer-result.correct h3 {
      color: #2e7d32;
    }

    .answer-result.incorrect h3 {
      color: #c62828;
    }

    .answer-result p {
      margin: 8px 0;
      font-size: 16px;
      color: #333;
    }

    .explanation {
      margin-top: 24px;
      padding: 16px;
      background-color: rgba(255,255,255,0.5);
      border-radius: 8px;
      border-left: 4px solid #2196f3;
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

    .waiting-organizer {
      margin-top: 32px;
      padding: 24px;
      background-color: #f5f5f5;
      border-radius: 8px;
      text-align: center;
    }

    .waiting-message {
      margin-top: 24px;
      font-size: 16px;
      color: #666;
      font-style: italic;
    }

    @media (max-width: 600px) {
      .game-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 12px;
      }

      .question-text {
        font-size: 18px;
      }

      .vote-answer {
        min-width: 80px;
        font-size: 14px;
      }

      .answer-result {
        padding: 24px 16px;
      }
    }
  `]
})
export class GamePlayComponent implements OnInit, OnDestroy {
  @Input() gameId!: number;
  @Output() gameCompleted = new EventEmitter<void>();

  private gamesApi = inject(GamesApiService);
  private authApi = inject(AuthApiService);

  game = signal<GameDto | null>(null);
  stats = signal<GameStatsDto | null>(null);
  loading = signal(true);
  error = signal<string | null>(null);
  submitting = signal(false);
  hasVoted = signal(false);
  revealing = signal(false);
  movingNext = signal(false);
  selectedOption = signal<string | null>(null);

  userAnswer = '';
  currentUserId: number | null = null;

  private statsSubscription?: Subscription;
  Object = Object; // Expose Object to template

  ngOnInit() {
    // Get current user ID first
    this.authApi.me().pipe(take(1)).subscribe({
      next: (me) => {
        this.currentUserId = me?.id ?? null;
        this.loadGame();
        this.startStatsPolling();
      },
      error: () => {
        this.error.set('Failed to load user information');
        this.loading.set(false);
      }
    });
  }

  ngOnDestroy() {
    this.stopStatsPolling();
  }

  loadGame() {
    this.loading.set(true);
    this.error.set(null);

    this.gamesApi.get(this.gameId).subscribe({
      next: (game) => {
        this.game.set(game);
        this.stats.set(game.stats);
        this.loading.set(false);

        // Check if current user has already voted
        this.checkUserVote(game);

        // Stop polling if game is completed
        if (game.status === 'COMPLETED') {
          this.stopStatsPolling();
          this.gameCompleted.emit();
        }
      },
      error: (err) => {
        this.loading.set(false);
        this.error.set(err.error?.detail || err.message || 'Failed to load game');
      }
    });
  }

  startStatsPolling() {
    // Poll stats every 3 seconds while game is active or showing results
    this.statsSubscription = interval(3000)
      .pipe(
        takeWhile(() => {
          const status = this.game()?.status;
          return status === 'ACTIVE' || status === 'SHOWING_RESULTS';
        }, true), // Include final value
        switchMap(() => this.gamesApi.get(this.gameId))
      )
      .subscribe({
        next: (game) => {
          const previousQuestionIndex = this.game()?.current_question_index;
          const previousStatus = this.game()?.status;

          this.game.set(game);
          this.stats.set(game.stats);

          // Check if user has voted for current question
          this.checkUserVote(game);

          // If question changed, reset vote state
          if (previousQuestionIndex !== undefined &&
              previousQuestionIndex !== game.current_question_index) {
            this.hasVoted.set(false);
            this.selectedOption.set(null);
            this.userAnswer = '';
          }

          // If status changed from SHOWING_RESULTS to ACTIVE, restart polling
          if (previousStatus === 'SHOWING_RESULTS' && game.status === 'ACTIVE') {
            this.stopStatsPolling();
            this.startStatsPolling();
          }

          if (game.status === 'COMPLETED') {
            this.stopStatsPolling();
            this.gameCompleted.emit();
          }
        },
        error: (err) => {
          console.error('Failed to update stats:', err);
        }
      });
  }

  stopStatsPolling() {
    if (this.statsSubscription) {
      this.statsSubscription.unsubscribe();
      this.statsSubscription = undefined;
    }
  }

  checkUserVote(game: GameDto) {
    // Check if current user has voted for the CURRENT question
    if (!this.currentUserId) {
      this.hasVoted.set(false);
      return;
    }
    // The votes array contains votes for the current question only
    // (backend filters by current_question_index)
    this.hasVoted.set(game.votes.some(v => v.user_id === this.currentUserId));
  }

  getUserVote(): string {
    const currentGame = this.game();
    if (!currentGame || !currentGame.votes.length || !this.currentUserId) {
      return '';
    }
    // Find and return the current user's vote
    const userVote = currentGame.votes.find(v => v.user_id === this.currentUserId);
    return userVote?.answer || '';
  }

  selectOption(option: string) {
    this.selectedOption.set(option);
  }

  onSubmitVote() {
    const answer = this.selectedOption();
    if (!answer || this.submitting()) {
      return;
    }

    this.submitting.set(true);
    this.error.set(null);

    this.gamesApi.vote(this.gameId, { answer: answer }).subscribe({
      next: (game) => {
        this.submitting.set(false);
        this.hasVoted.set(true);
        this.game.set(game);
        this.stats.set(game.stats);

        if (game.status === 'COMPLETED') {
          this.stopStatsPolling();
          this.gameCompleted.emit();
        }
      },
      error: (err) => {
        this.submitting.set(false);
        this.error.set(err.error?.detail || err.message || 'Failed to submit vote');
      }
    });
  }

  getVoteCountEntries(): [string, number][] {
    const voteCounts = this.stats()?.vote_counts || {};
    return Object.entries(voteCounts).sort((a, b) => b[1] - a[1]);
  }

  isOrganizer(): boolean {
    const currentGame = this.game();
    if (!currentGame || !this.currentUserId) {
      return false;
    }
    return currentGame.created_by_id === this.currentUserId;
  }

  onRevealAnswer() {
    if (this.revealing()) {
      return;
    }

    this.revealing.set(true);
    this.error.set(null);

    this.gamesApi.revealAnswer(this.gameId).subscribe({
      next: (response) => {
        this.revealing.set(false);
        this.game.set(response.game);
        this.stats.set(response.game.stats);

        // Keep polling so participants get the update
        // (polling continues while status is SHOWING_RESULTS)
      },
      error: (err) => {
        this.revealing.set(false);
        this.error.set(err.error?.detail || err.message || 'Failed to reveal answer');
      }
    });
  }

  onNextQuestion() {
    if (this.movingNext()) {
      return;
    }

    this.movingNext.set(true);
    this.error.set(null);

    this.gamesApi.nextQuestion(this.gameId).subscribe({
      next: (response) => {
        this.movingNext.set(false);

        if (response.next.status === 'completed') {
          // Game is completed
          this.game.set(response.game);
          this.gameCompleted.emit();
        } else {
          // Moved to next question
          this.game.set(response.game);
          this.stats.set(response.game.stats);
          this.hasVoted.set(false);
          this.selectedOption.set(null);
          this.userAnswer = '';

          // Restart polling for the new question
          this.startStatsPolling();
        }
      },
      error: (err) => {
        this.movingNext.set(false);
        this.error.set(err.error?.detail || err.message || 'Failed to move to next question');
      }
    });
  }
}
