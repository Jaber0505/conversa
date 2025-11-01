export type EventDto = {
  id: number;
  organizer: number;
  organizer_id: number;
  partner: number;
  partner_name: string;
  partner_city?: string;
  language: number;
  language_code: string;
  title: string;
  address: string;
  theme: string;
  difficulty: string;
  datetime_start: string;
  price_cents: number;
  photo?: string;
  status: string;
  published_at?: string;
  cancelled_at?: string;
  created_at: string;
  updated_at: string;
  _links?: any;
  // Frontend-only fields (computed)
  alreadyBooked?: boolean;
  is_cancelled?: boolean; // Computed from status === 'CANCELLED' or cancelled_at !== null
};

export type EventDetailDto = EventDto & {
  // Additional partner information
  partner_address: string;
  partner_capacity: number;
  // Additional language information
  language_name: string;
  // Organizer information
  organizer_first_name: string;
  organizer_last_name: string;
  // Computed fields
  participants_count: number;
  available_slots: number;
  is_full: boolean;
};

export type EventWrite = {
  title: string;
  city: string;
  address: string;
  venue_name: string;
  datetime_start: string;
  language: string;
  price_cents: number;
  max_seats: number;
};

export type EventCreatePayload = {
  partner: number;
  language: number;
  theme: string;
  difficulty: string;
  datetime_start: string;
};

export type EventUpdate = Partial<EventWrite>;
