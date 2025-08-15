import { ID } from './common.model';

// Lecture
export type Event = {
  id: ID;
  title: string;               // maxLength 140
  city: string;                // maxLength 80
  address: string;             // maxLength 200
  venue_name: string;          // maxLength 140
  datetime_start: string;      // ISO 8601
  language: string;            // readOnly (code langue)
  price_cents: number;         // >=0
  max_seats: number;           // >=0
  is_cancelled: boolean;       // readOnly
};

// Écriture (create/update)
export type EventWrite = {
  title: string;
  city: string;
  address: string;
  venue_name: string;
  datetime_start: string;      // ISO 8601
  language: string;            // code langue
  price_cents: number;
  max_seats: number;
};

export type EventUpdate = Partial<EventWrite>; // PATCH
