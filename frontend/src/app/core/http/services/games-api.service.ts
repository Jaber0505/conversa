import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from '@core/http';
import {
  GameDto,
  GameCreatePayload,
  VoteSubmitPayload,
  GameStatsDto,
  GameListParams,
  DetailedResultsDto,
  GameResultDto
} from '@app/core/models/games.model';

@Injectable({ providedIn: 'root' })
export class GamesApiService {
  private http = inject(HttpClient);
  private base = inject(API_URL);

  /**
   * List games for events user has access to.
   * @param params Optional filters (event_id, status)
   */
  list(params?: GameListParams): Observable<GameDto[]> {
    let httpParams = new HttpParams();
    if (params?.event_id != null) httpParams = httpParams.set('event_id', String(params.event_id));
    if (params?.status) httpParams = httpParams.set('status', params.status);
    return this.http.get<GameDto[]>(`${this.base}/games/`, { params: httpParams });
  }

  /**
   * Get game details by ID.
   * @param id Game ID
   */
  get(id: number): Observable<GameDto> {
    return this.http.get<GameDto>(`${this.base}/games/${id}/`);
  }

  /**
   * Create a new game (organizer only).
   * @param payload Game creation data
   */
  create(payload: GameCreatePayload): Observable<GameDto> {
    return this.http.post<GameDto>(`${this.base}/games/create/`, payload);
  }

  /**
   * Submit a vote for a game (confirmed participants only).
   * @param gameId Game ID
   * @param payload Vote data
   */
  vote(gameId: number, payload: VoteSubmitPayload): Observable<GameDto> {
    return this.http.post<GameDto>(`${this.base}/games/${gameId}/vote/`, payload);
  }

  /**
   * Get real-time game statistics.
   * @param gameId Game ID
   */
  getStats(gameId: number): Observable<GameStatsDto> {
    return this.http.get<GameStatsDto>(`${this.base}/games/${gameId}/stats/`);
  }

  /**
   * Get the active game for an event.
   * @param eventId Event ID
   */
  getActiveGame(eventId: number): Observable<GameDto> {
    const httpParams = new HttpParams().set('event_id', String(eventId));
    return this.http.get<GameDto>(`${this.base}/games/active/`, { params: httpParams });
  }

  /**
   * Reveal the answer for the current question (organizer only).
   * @param gameId Game ID
   */
  revealAnswer(gameId: number): Observable<{ game: GameDto; reveal: any }> {
    return this.http.post<{ game: GameDto; reveal: any }>(
      `${this.base}/games/${gameId}/reveal-answer/`,
      {}
    );
  }

  /**
   * Move to next question or complete game (organizer only).
   * @param gameId Game ID
   */
  nextQuestion(gameId: number): Observable<{ game: GameDto; next: any }> {
    return this.http.post<{ game: GameDto; next: any }>(
      `${this.base}/games/${gameId}/next-question/`,
      {}
    );
  }

  /**
   * Get detailed results for each question in a completed game.
   * @param gameId Game ID
   */
  getDetailedResults(gameId: number): Observable<DetailedResultsDto> {
    return this.http.get<DetailedResultsDto>(`${this.base}/games/${gameId}/detailed-results/`);
  }

  /**
   * Get final summary with badges for a completed game.
   * @param gameId Game ID
   */
  getSummary(gameId: number): Observable<GameResultDto> {
    return this.http.get<GameResultDto>(`${this.base}/games/${gameId}/summary/`);
  }
}
