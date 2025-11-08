/**
 * Registration models for free event sign-ups.
 */

export interface Registration {
  id: number;
  user: number;
  user_email?: string;
  user_first_name?: string;
  user_last_name?: string;
  event: number;
  event_id?: number;
  has_booking?: boolean;
  notified_publication: boolean;
  created_at: string;
  updated_at: string;
}

export interface RegistrationCreatePayload {
  event: number;
}
