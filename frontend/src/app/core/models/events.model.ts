export type EventDto = {
  id: number;
  title: string;
  city: string;
  address: string;
  venue_name: string;
  partner_name: string;
  datetime_start: string;
  theme: string;
  language_code: string;
  price_cents: number;
  max_seats: number;
  is_cancelled: boolean;
  alreadyBooked: boolean;
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

export type EventUpdate = Partial<EventWrite>;
