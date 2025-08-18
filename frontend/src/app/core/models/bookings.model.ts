import { ID } from './common.model';

export type StatusEnum = 'pending' | 'paid' | 'cancelled' | string; // la spec expose un enum string

// Lecture
export type BookingStatus = 'confirmed' | 'waiting_for_payment' | 'cancelled_user';

export interface Booking {
  id: number;
  event: number;        // id de l'événement
  user: number;         // id du user
  status: BookingStatus;
  event_start: string;  // ISO date-time (server: serializer)
  created_at: string;   // ISO
  updated_at: string;   // ISO
}




