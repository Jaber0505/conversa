import {EventDto} from "@app/core/models/events.model";

export type StatusEnum = 'pending' | 'paid' | 'cancelled' | string;

// Lecture
export type BookingStatus = 'confirmed' | 'waiting_for_payment' | 'cancelled_user';

export interface Booking {
  id: number;
  public_id: string;
  user: number;
  event: number;
  eventObject?: EventDto;
  status: string;
  amount_cents: number;
  currency: string;
  expires_at: string | null;
  confirmed_at: string | null;
  cancelled_at: string | null;
  confirmed_after_expiry: boolean;
  created_at: string;
  updated_at: string;
}




