import { ID } from './common.model';

export type StatusEnum = 'pending' | 'paid' | 'cancelled' | string; // la spec expose un enum string

// Lecture
export type Booking = {
  id: ID;
  event: {
    id: ID;
    title: string;
    venue_name: string;
    datetime_start: string;
    city: string;
    address: string;
    language: string;
  };                           // la spec référence Event (readOnly)
  seats: number;               // min 1
  amount_cents: number;        // >=0
  created_at: string;          // ISO
  status: StatusEnum;          // readOnly
};

// Création
export type BookingCreate = {
  event: ID;                   // référence
  seats: number;               // min 1
};
