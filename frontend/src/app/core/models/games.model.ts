/**
 * Game models for Conversa language learning games.
 */

export type GameType = 'picture_description' | 'word_association' | 'debate' | 'role_play';
export type GameDifficulty = 'easy' | 'medium' | 'hard';
export type GameStatus = 'ACTIVE' | 'SHOWING_RESULTS' | 'COMPLETED';

export interface GameVoteDto {
  id: number;
  user_id: number;
  user_email: string;
  answer: string;
  created_at: string;
}

export interface GameStatsDto {
  total_votes: number;
  confirmed_participants: number;
  vote_counts: { [answer: string]: number };
  votes_remaining: number;
}

export interface GameDto {
  id: number;
  public_id: string;
  event_id: number;
  created_by_id: number;
  created_by_email: string;
  game_type: GameType;
  difficulty: GameDifficulty;
  language_code: string;
  // Multi-question support
  current_question_index: number;
  total_questions: number;
  answer_revealed: boolean;
  // Current question
  question_id: string;
  question_text: string;
  correct_answer: string;
  options: string[];
  context?: string;
  image_url?: string;
  status: GameStatus;
  completed_at?: string;
  is_correct?: boolean;
  final_answer?: string;
  votes: GameVoteDto[];
  stats: GameStatsDto;
  created_at: string;
  updated_at: string;
  _links?: any;
}

export interface GameCreatePayload {
  event_id: number;
  game_type: GameType;
}

export interface VoteSubmitPayload {
  answer: string;
}

export interface GameListParams {
  event_id?: number;
  status?: GameStatus;
}

// Badge and Results types
export type BadgeType = 'victory' | 'participation';

export interface BadgeDto {
  id: number;
  user_email: string;
  badge_type: BadgeType;
  earned_at: string;
}

export interface GameResultDto {
  id: number;
  game_id: number;
  game_public_id: string;
  total_questions: number;
  correct_answers: number;
  score_percentage: number;
  badge_type: BadgeType;
  victory_threshold: number;
  badges: BadgeDto[];
  created_at: string;
}

export interface QuestionVoteDto {
  user_id: number;
  user_email: string;
  answer: string;
  created_at: string;
}

export interface QuestionResultDto {
  question_index: number;
  question_id: string;
  question_text: string;
  image_url?: string;
  options: string[];
  correct_answer: string;
  context?: string;
  team_answer: string | null;
  is_correct: boolean;
  votes: QuestionVoteDto[];
  total_votes: number;
}

export interface DetailedResultsDto {
  game_id: number;
  game_public_id: string;
  total_questions: number;
  questions: QuestionResultDto[];
}
